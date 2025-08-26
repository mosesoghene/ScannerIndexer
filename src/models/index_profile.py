from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class IndexField:
    """Represents a single indexing field"""
    name: str
    value: str = ""
    placeholder: str = ""
    required: bool = False
    field_type: str = "text"  # text, date, number, dropdown
    options: List[str] = field(default_factory=list)  # For dropdown fields

    def validate(self) -> tuple[bool, str]:
        """Validate field value"""
        if self.required and not self.value.strip():
            return False, f"{self.name} is required"
        return True, ""


@dataclass
class IndexProfile:
    """A collection of index fields that can be applied to pages"""
    name: str
    description: str = ""
    fields: List[IndexField] = field(default_factory=list)
    output_pattern: str = "{folder_name}/{file_name}"  # Pattern for output path
    input_folder: str = ""
    output_folder: str = ""

    def add_field(self, field: IndexField):
        """Add a field to this profile"""
        self.fields.append(field)

    def remove_field(self, field_name: str) -> bool:
        """Remove a field by name"""
        original_len = len(self.fields)
        self.fields = [f for f in self.fields if f.name != field_name]
        return len(self.fields) < original_len

    def get_field(self, name: str) -> Optional[IndexField]:
        """Get a field by name"""
        return next((f for f in self.fields if f.name == name), None)

    def validate_all_fields(self) -> tuple[bool, List[str]]:
        """Validate all fields"""
        errors = []
        for field in self.fields:
            valid, error = field.validate()
            if not valid:
                errors.append(error)
        return len(errors) == 0, errors

    def generate_output_path(self, base_dir: str) -> str:
        """Generate output path based on field values and pattern"""
        replacements = {}

        # Add field values
        for field in self.fields:
            key = field.name.lower().replace(" ", "_")
            replacements[key] = field.value.strip() or "unknown"

        # Default replacements
        replacements.setdefault("folder_name", "extracted")
        replacements.setdefault("file_name", "document")

        try:
            relative_path = self.output_pattern.format(**replacements)
            return str(Path(base_dir) / relative_path)
        except KeyError as e:
            # Fallback if pattern has undefined keys
            return str(Path(base_dir) / replacements.get("folder_name", "extracted") / replacements.get("file_name",
                                                                                                        "document"))

    def clone(self) -> 'IndexProfile':
        """Create a copy of this profile"""
        return IndexProfile(
            name=f"{self.name} (Copy)",
            description=self.description,
            fields=[IndexField(
                name=f.name,
                value=f.value,
                placeholder=f.placeholder,
                required=f.required,
                field_type=f.field_type,
                options=f.options.copy()
            ) for f in self.fields],
            output_pattern=self.output_pattern
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'description': self.description,
            'output_pattern': self.output_pattern,
            'input_folder': self.input_folder,
            'output_folder': self.output_folder,
            'fields': [
                {
                    'name': f.name,
                    'value': f.value,
                    'placeholder': f.placeholder,
                    'required': f.required,
                    'field_type': f.field_type,
                    'options': f.options
                }
                for f in self.fields
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'IndexProfile':
        """Create from dictionary"""
        fields = [
            IndexField(
                name=f['name'],
                value=f.get('value', ''),
                placeholder=f.get('placeholder', ''),
                required=f.get('required', False),
                field_type=f.get('field_type', 'text'),
                options=f.get('options', [])
            )
            for f in data.get('fields', [])
        ]

        return cls(
            name=data['name'],
            description=data.get('description', ''),
            fields=fields,
            output_pattern=data.get('output_pattern', '{folder_name}/{file_name}'),
            input_folder = data.get('input_folder', ''),
            output_folder = data.get('output_folder', '')
        )


class ProfileManager:
    """Manages saving/loading of index profiles"""

    def __init__(self, profiles_file: str = "profiles.json"):
        self.profiles_file = Path(profiles_file)
        self.profiles: List[IndexProfile] = []
        self.load_profiles()

    def load_profiles(self):
        """Load profiles from file"""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    self.profiles = [IndexProfile.from_dict(p) for p in data]
            except Exception as e:
                print(f"Error loading profiles: {e}")
                self.profiles = []

        # Add default profiles if none exist
        if not self.profiles:
            self.create_default_profiles()

    def save_profiles(self):
        """Save profiles to file"""
        try:
            with open(self.profiles_file, 'w') as f:
                data = [p.to_dict() for p in self.profiles]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")

    def add_profile(self, profile: IndexProfile):
        """Add a new profile"""
        self.profiles.append(profile)
        self.save_profiles()

    def remove_profile(self, profile_name: str) -> bool:
        """Remove a profile by name"""
        original_len = len(self.profiles)
        self.profiles = [p for p in self.profiles if p.name != profile_name]
        if len(self.profiles) < original_len:
            self.save_profiles()
            return True
        return False

    def get_profile(self, name: str) -> Optional[IndexProfile]:
        """Get a profile by name"""
        return next((p for p in self.profiles if p.name == name), None)

    def create_default_profiles(self):
        """Create some default profiles"""
        # Basic document profile
        basic = IndexProfile(
            name="Basic Document",
            description="Simple document indexing",
            output_pattern="{document_type}/{file_name}"
        )
        basic.add_field(IndexField("Document Type", placeholder="e.g., contracts, invoices"))
        basic.add_field(IndexField("File Name", placeholder="Output filename", required=True))

        # Invoice profile
        invoice = IndexProfile(
            name="Invoice Processing",
            description="For processing invoices",
            output_pattern="{vendor}/{year}/{month}/{invoice_number}"
        )
        invoice.add_field(IndexField("Vendor", placeholder="Vendor name", required=True))
        invoice.add_field(IndexField("Invoice Number", placeholder="Invoice #", required=True))
        invoice.add_field(IndexField("Year", placeholder="2024", required=True))
        invoice.add_field(IndexField("Month", placeholder="01-12", required=True))

        # Contract profile
        contract = IndexProfile(
            name="Contract Management",
            description="For organizing contracts",
            output_pattern="{contract_type}/{client}/{file_name}"
        )
        contract.add_field(IndexField("Contract Type", "Service Agreement", "Contract type"))
        contract.add_field(IndexField("Client", placeholder="Client name", required=True))
        contract.add_field(IndexField("File Name", placeholder="Contract filename", required=True))

        self.profiles.extend([basic, invoice, contract])
        self.save_profiles()