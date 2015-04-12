#!/usr/bin/env python

'''A utility for reading the master boot record (MBR) and FAT 16/32 partition
headers from a raw image file.
CSE 469 Course Project
'''

import sys

class Field:
	pass

class IntField(Field):
	def __init__(self, offset, length, display, endianness):
		self.offset = offset
		self.length = length
		self.display = display
		self.endianness = endianness

	def read(self, buf, struct_offset):
		offset = self.offset + struct_offset
		field = buf[offset:offset + self.length]
		return int.from_bytes(field, byteorder=self.endianness)

	def extract(self, buf, struct_offset):
		value = self.read(buf, struct_offset)
		if self.display == 'hex':
			return hex(value)
		return str(value)

class EnumField(IntField):
	def __init__(self, offset, length, endianness, values):
		super().__init__(offset, length, 'decimal', endianness)
		self.values = values

	def extract(self, buf, struct_offset):
		value = self.read(buf, struct_offset)
		if value in self.values:
			return self.values[value]
		return '? ({0})'.format(hex(value))

class StringField(Field):
	def __init__(self, offset, max_length, encoding='utf-8'):
		self.offset = offset
		self.max_length = max_length

	def extract(self, buf, struct_offset):
		offset = self.offset + struct_offset
		# Find terminating null character, if there is one.
		index = buf.find(0, offset)
		if index == -1:
			end = offset + self.max_length
		else:
			end = offset + min(index, self.max_length)
		return buf[offset:end].decode(encoding=self.encoding)

class Struct:
	def __init__(self):
		pass

	def extract(self, buf, offset):
		results = {}
		for attr, value in self.__dict__.items():
			if isinstance(value, Field):
				results[attr] = value.extract(buf, offset)
		return results

mbr_entry = Struct()
mbr_entry.current_state = EnumField(0x00, 1, 'little', {0x00: 'Inactive', 0x80: 'Active'})
mbr_entry.beginning_head = IntField(0x01, 1, 'decimal', 'little')
mbr_entry.beginning_cylinder = IntField(0x02, 2, 'decimal', 'little')
mbr_entry.partition_type = EnumField(0x04, 1, 'little', {
	0x01: 'FAT12',
	0x04: 'FAT16',
	0x05: 'Extended partition',
	0x06: 'FAT16',
	0x07: 'NTFS',
	0x0B: 'FAT32',
	0x0C: 'FAT32',
	0x81: 'Linux',
	0x82: 'Linux swap',
	0x83: 'Linux native FS'
})
mbr_entry.end_head = IntField(0x05, 1, 'decimal', 'little')
mbr_entry.end_cylinder = IntField(0x06, 2, 'decimal', 'little')
mbr_entry.sectors_before_partition = IntField(0x08, 4, 'decimal', 'little')
mbr_entry.sectors_in_partition = IntField(0x0C, 4, 'decimal', 'little')

def main():
	path = sys.argv[1]
	with open(path, 'rb') as f:
		buf = f.read(512)
	print(mbr_entry.extract(buf, 0x01BE))
	print(mbr_entry.extract(buf, 0x01CE))
	print(mbr_entry.extract(buf, 0x01DE))
	print(mbr_entry.extract(buf, 0x01EE))

if __name__ == '__main__':
	main()