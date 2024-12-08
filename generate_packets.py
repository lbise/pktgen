#!/usr/bin/env python3
import argparse
import os

import yaml


class PacketField:
    def __init__(self, name, size, byte_offset, bit_offset):
        self.name = name
        self.description = None
        self.values = {}
        self.size = size
        self.byte_offset = byte_offset
        self.bit_offset = bit_offset

    def __repr__(self):
        repr = f"{self.__class__.__name__}: {self.name} {self.description} size={self.size} byte_offset={self.byte_offset} bit_offset={self.bit_offset}"
        return repr

    def generate_enum(self, packet):
        enum = []
        enum.append(f"enum Dm{packet.name}{self.name} {{")
        for key, val in self.values.items():
            enum.append(
                f"    {to_upper_snake_case(self.name)}_{to_upper_snake_case(val)} = {key},"
            )

        enum.append("};\n")
        return enum

    def generate_macros_bits(self, packet, macro_name, byte_offset_macro):
        content = []
        bit_offset_macro = (
            f"{packet.prefix}_{packet.name.upper()}_{macro_name}_BIT_OFFSET"
        )
        content.append(f"#define {bit_offset_macro} {self.bit_offset}")
        size_macro = f"{packet.prefix}_{packet.name.upper()}_{macro_name}_SIZE_BITS"
        content.append(f"#define {size_macro} {self.size}")

        # Get/Set macros
        content.append(
            f"#define {packet.prefix}_GET_{packet.name.upper()}_{macro_name}(packet) \\\n"
            f"    GET_BITS(packet, {byte_offset_macro}, {bit_offset_macro}, {size_macro})"
        )
        content.append(
            f"#define {packet.prefix}_SET_{packet.name.upper()}_{macro_name}(packet, val) \\\n"
            f"    SET_BITS(packet, {byte_offset_macro}, {bit_offset_macro}, {size_macro})"
        )
        return content

    def generate_macros_bytes(self, packet, macro_name, byte_offset_macro):
        content = []
        # Multiple of byte field
        size_macro = f"{packet.prefix}_{packet.name.upper()}_{macro_name}_SIZE_BYTES"
        content.append(f"#define {size_macro} {int(self.size / 8)}")

        # Get/Set macros
        content.append(
            f"#define {packet.prefix}_GET_{packet.name.upper()}_{macro_name}(packet) \\\n"
            f"    GET_UINT{self.size}(packet, {byte_offset_macro}, {size_macro})"
        )
        content.append(
            f"#define {packet.prefix}_SET_{packet.name.upper()}_{macro_name}(packet, val) \\\n"
            f"    SET_UINT{self.size}(packet, {byte_offset_macro}, {size_macro}, val)"
        )
        return content

    def generate(self, packet):
        content = []

        # Create enum for field values
        if self.values:
            content.extend(self.generate_enum(packet))

        macro_name = self.name.replace(" ", "_").upper()
        byte_offset_macro = (
            f"{packet.prefix}_{packet.name.upper()}_{macro_name}_BYTE_OFFSET"
        )
        content.append(f"#define {byte_offset_macro} {self.byte_offset}")

        if self.bit_offset is not None:
            # Field is smaller than a byte
            content.extend(
                self.generate_macros_bits(packet, macro_name, byte_offset_macro)
            )
            size_str = f"{self.size}bits"
        else:
            content.extend(
                self.generate_macros_bytes(packet, macro_name, byte_offset_macro)
            )
            size_str = f"{int(self.size / 8)}bytes"

        content.insert(0, f"// +++ {self.name} ({size_str}) +++")

        content.append("")

        return content


class Packet:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.prefix = None
        self.byte_offset = 0
        self.bit_offset = 8
        self.fields = []

    def __repr__(self):
        fieldsstr = ""
        for field in self.fields:
            fieldsstr += f"{field}\n"

        repr = f"{self.__class__.__name__}: {self.name} fields=len={len(self.fields)} \n{fieldsstr}"
        return repr

    def update_offsets(self, size):
        if size < 8:
            self.bit_offset -= size
            if self.bit_offset == 0:
                self.bit_offset = 8
                self.byte_offset += 1
        else:
            self.byte_offset += int(size / 8)

    @staticmethod
    def find_packet(packets, name):
        for packet in packets:
            if packet.name == name:
                return packet

        return None

    def process_fields(self, fields, all_packets):
        for field in fields:
            name = field.get("name", None)
            ref = field.get("reference", None)
            size = field.get("size")
            field_type = field.get("type", "single")
            values = field.get("values", None)
            if ref:
                # Reference to another packet
                packet = self.find_packet(all_packets, ref)
                assert packet, f"Reference not found: {ref}"
                # Take into account the size of each field of the reference
                for pktfield in packet.fields:
                    self.update_offsets(pktfield.size)
            elif field_type == "structure":
                # Nested definition
                self.process_fields(fields["fields"], all_packets)
            else:
                # New field
                bit_offset = None
                if size < 8:
                    bit_offset = self.bit_offset - size

                field = PacketField(name, size, self.byte_offset, bit_offset)
                if "description" in fields:
                    field.description = fields["description"]

                if values:
                    field.values = values

                self.update_offsets(size)

                self.fields.append(field)

    def generate(self):
        content = []
        content.append(f"// ****** {self.name} ******")
        if self.description:
            content.append(f"// {self.description}")

        for field in self.fields:
            content.extend(field.generate(self))

        return content


class DmPacketParser:

    def __init__(self, file):
        self.file = file
        self.packets = []
        self.byte_offset = 0
        self.bit_offset = 0
        self.prefix = "DMPKT"

    def get_reference(self, name):
        return self.packets[name]

    def is_byte_aligned(self, size):
        byte_mult = (size % 8) == 0
        return byte_mult and (self.bit_offset == 8 or self.bit_offset == 0)

    # def process_fields(self, packet_name, fields, field_func):
    #    content = []
    #    for field in fields:
    #        name = field.get("name", None)
    #        ref = field.get("reference", None)
    #        merge = field.get("merge", None)
    #        size = field.get("size")
    #        field_type = field.get("type", "single")
    #        values = field.get("values", None)

    #        if ref:
    #            # Reference to another description
    #            refdesc = self.get_reference(ref)
    #            content.append(f"// {ref}")
    #            desc = refdesc.get("description", None)
    #            if desc:
    #                content.append(f"// {desc}")

    #            # Take into account fields sizes
    #            nested_macros = self.process_fields(
    #                packet_name + to_camel_case(ref),
    #                refdesc["fields"],
    #                self.upate_offset_field,
    #            )
    #        elif merge:
    #            # Special merge field
    #            tomerge = field["merge"]
    #            fieldname = self.get_field_to_merge(tomerge)
    #            cont = self.merge_fields(fieldname, tomerge)
    #        elif field_type == "array":
    #            # Array definition
    #            content.append(f"// {name}: Array of {size} bytes")
    #            content.append(
    #                f"#define {packet_name.upper()}_{name.upper()}_OFFSET {self.bit_offset}"
    #            )
    #            content.append(
    #                f"#define {packet_name.upper()}_{name.upper()}_SIZE_BYTES {size}"
    #            )
    #            self.bit_offset += int(size) * 8
    #        elif field_type == "structure":
    #            # Nested definition
    #            content.append(f"// {name}: Nested structure")
    #            nested_macros = self.process_fields(
    #                packet_name + to_camel_case(name),
    #                field["fields"],
    #                self.generate_single_field,
    #            )
    #            content.extend(nested_macros)
    #        else:
    #            desc = None
    #            if "description" in fields:
    #                desc = fields["description"]

    #            cont = field_func(packet_name, name, desc, size, values)
    #            if cont:
    #                content.extend(cont)

    #    return content

    @staticmethod
    def generate_comment():
        content = "// This is the header of the file\n"
        content += "// This is a generated file.\n"
        return content

    def generate(self, description):
        content = []
        hdr = self.generate_comment()
        content.append(hdr)

        packets = []

        # Parse all packets/fields into classes
        for packet_name, packet_data in description.items():
            desc = None
            if "description" in packet_data:
                desc = packet_data["description"]

            packet = Packet(packet_name, desc)
            packet.prefix = self.prefix
            packet.process_fields(packet_data["fields"], packets)
            packets.append(packet)

        for packet in packets:
            content.extend(packet.generate())

        return content

    def parse(self):
        with open(self.file, "r") as f:
            description = yaml.safe_load(f)

        self.packets = description
        return self.generate(self.packets)


def parse_packet_yaml(file_path):
    """Parse a YAML file describing packet formats."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def to_camel_case(s):
    # Split the string into words
    words = s.split()
    # Capitalize the first letter of each word and join them together
    camel_case_string = "".join(word.capitalize() for word in words)
    return camel_case_string


def to_upper_snake_case(s):
    # Replace spaces with underscores and convert to uppercase
    upper_snake_case_string = s.replace(" ", "_").upper()
    return upper_snake_case_string


def main():
    parser = argparse.ArgumentParser(description="Generate packets")
    parser.add_argument("description", help="Packet description file")
    parser.add_argument("output", help="Output directory for generated files")
    args = parser.parse_args()

    if not os.path.exists(args.description):
        print(f"File does not exist: {args.description}")
        return

    if not os.path.exists(args.output):
        print(f"Output directory does not exist: {args.output}")
        return

    dmparser = DmPacketParser(args.description)
    content = dmparser.parse()

    for l in content:
        print(f"{l}")

    # Write to file
    outfile = os.path.join(args.output, "dmtx_packet_gen.h")
    with open(outfile, "w") as f:
        f.write("\n".join(content))

    return

    # Load packet definitions from a YAML file
    packets = parse_packet_yaml(args.file)

    definitions = {}
    content = []
    for packet_name, packet_data in packets.items():
        if packet_data["deftype"] == "definition":
            # Save definitions
            defs = generate_defs_macros(
                to_camel_case(packet_name), packet_data["fields"], packets
            )
            content.append(defs)
            continue

        print(f"// *** {packet_name} ***")
        macros = generate_field_macros(
            to_camel_case(packet_name), packet_data["fields"], packets
        )
        content.append(macros)
        print("\n".join(macros))
        print("\n")

    # for def in definitions:
    #    macros = generate


if __name__ == "__main__":
    main()
