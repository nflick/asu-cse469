#!/usr/bin/python3

'''A utility for reading the master boot record (MBR) and FAT 16/32 partition
headers from a raw image file.
CSE 469 Course Project
'''

import sys
import argparse
import os.path
import hashlib
import math

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
		self.encoding = encoding

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
mbr_entry.partition_type = IntField(0x04, 1, 'hex', 'little')
mbr_entry.partition_type_str = EnumField(0x04, 1, 'little', {
	0x01: 'DOS 12-bit FAT',
	0x04: 'DOS 16-bit FAT for partitions smaller than 32MB',
	0x05: 'Extended partition',
	0x06: 'DOS 16-bit FAT for partitions larger than 32MB',
	0x07: 'NTFS',
	0x08: 'AIX bootable partition',
	0x09: 'AIX data partition',
	0x0B: 'DOS 32-bit FAT',
	0x0C: 'DOS 32-bit FAT for interrupt 13 support',
	0x17: 'Hidden NTFS partition (XP and earlier)',
	0x1B: 'Hidden FAT32 partition',
	0x1E: 'Hidden VFAT partition',
	0x3C: 'Partition Magic recovery partition',
	0x66: 'Novell partitions',
	0x67: 'Novell partitions',
	0x68: 'Novell partitions',
	0x69: 'Novell partitions',
	0x81: 'Linux',
	0x82: 'Linux swap partition (can also be associated with Solaris partitions)',
	0x83: 'Linux native file systems (Ext2, Ext3, Reiser, xiafs)',
	0x86: 'FAT16 volume/stripe set (Windows NT)',
	0x87: 'High Performance File System (HPFS) fault-tolerant mirrored partition or NTFS volume/strip set',
	0xA5: 'FreeBSD and BSD/386',
	0xA6: 'OpenBSD',
	0xA9: 'NetBSD',
	0xC7: 'Typical of a corrupted NTFS volume/stripe set',
	0xEB: 'BeOS'
})
mbr_entry.end_head = IntField(0x05, 1, 'decimal', 'little')
mbr_entry.end_cylinder = IntField(0x06, 2, 'decimal', 'little')
mbr_entry.sectors_before_partition = IntField(0x08, 4, 'decimal', 'little')
mbr_entry.sectors_in_partition = IntField(0x0C, 4, 'decimal', 'little')

vbr_sector = Struct()
vbr_sector.oem_name = StringField(3, 7)
vbr_sector.bytes_per_sector = IntField(11, 2, 'decimal', 'little')
vbr_sector.sectors_per_cluster = IntField(13, 1, 'decimal', 'little')
vbr_sector.reserved_sectors = IntField(14, 2, 'decimal', 'little')
vbr_sector.num_fat_tables = IntField(16, 1, 'decimal', 'little')
vbr_sector.max_root_files = IntField(17, 2, 'decimal', 'little')
vbr_sector.num_sectors_16 = IntField(19, 2, 'decimal', 'little')
vbr_sector.fat_table_size = IntField(22, 2, 'decimal', 'little')
vbr_sector.sectors_per_track = IntField(24, 2, 'decimal', 'little')
vbr_sector.num_heads = IntField(26, 2, 'decimal', 'little')
vbr_sector.partition_offset = IntField(28, 4, 'decimal', 'little')
vbr_sector.num_sectors = IntField(32, 4, 'decimal', 'little')
vbr_sector.fat_table_size32 = IntField(36, 4, 'decimal', 'little')

def build_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument('imagepath')
	return parser

def checksum(path, prefix, algo):
	with open(path, 'rb') as f:
		block = f.read(16384)
		while len(block) > 0:
			algo.update(block)
			block = f.read(16384)
	digest = algo.hexdigest()
	parent, basename = os.path.split(path)
	digestpath = os.path.join(parent, prefix + basename)
	with open(digestpath, 'w') as f:
		f.write(digest + '\n')
	return digest

def to_int(s):
	if s.startswith('0x'):
		return int(s, 16)
	return int(s)

def extract_mbr(f):
	f.seek(0)
	block = f.read(512)
	entries = [mbr_entry.extract(block, 0x01BE + 0x10 * i) for i in range(4)]
	for entry in entries:
		print('({0}) {1}, {2:}, {3}'.format(entry['partition_type'][2:].zfill(2), entry['partition_type_str'],
			entry['sectors_before_partition'].zfill(10), entry['sectors_in_partition'].zfill(10)))
	return entries

def extract_vbr(f, entry):
	byte_offset = to_int(entry['sectors_before_partition']) * 512
	f.seek(byte_offset)
	block = f.read(512)
	vbr = vbr_sector.extract(block, 0)

	fat32 = False
	if to_int(entry['partition_type']) == 0xB or to_int(entry['partition_type']) == 0xC:
		fat32 = True

	print('Reserved area: Start sector: {0} Ending sector: {1} Size: {2} sectors'.format(
		0, to_int(vbr['reserved_sectors']) - 1, vbr['reserved_sectors']))
	print('Sectors per cluster: {0} sectors'.format(vbr['sectors_per_cluster']))
	fat_size = to_int(vbr['fat_table_size32']) if fat32 else to_int(vbr['fat_table_size'])
	fat_end = to_int(vbr['reserved_sectors']) + fat_size * to_int(vbr['num_fat_tables'])
	print('FAT area:  Start sector: {0} Ending sector: {1}'.format(
		vbr['reserved_sectors'], fat_end - 1))
	print('# of FATs: {0}'.format(vbr['num_fat_tables']))
	print('The size of each FAT: {0} sectors'.format(fat_size))

	if fat32:
		cluster2 = fat_end
	else:
		# Fat 16. Need to offset for root directory entries.
		cluster2 = fat_end + int(math.ceil(to_int(vbr['max_root_files']) / 16))

	cluster2 += to_int(entry['sectors_before_partition'])
	print('The first sector of cluster 2: {0} sectors'.format(cluster2))


def run(args):
	print()
	print('Checksums:')
	print('=' * 50)
	print('MD5: ' + checksum(args.imagepath, 'MD5-', hashlib.md5()))
	print()
	print('SHA1: ' + checksum(args.imagepath, 'SHA1-', hashlib.sha1()))
	print('=' * 50)
	
	with open(args.imagepath, 'rb') as f:
		entries = extract_mbr(f)
		print('=' * 50)
		for i, entry in enumerate(entries):
			type_ = to_int(entry['partition_type'])
			if type_ == 4 or type_ == 6 or type_ == 0xB or type_ == 0xC:
				print('Partition {0} ({1}):'.format(i, entry['partition_type_str']))
				extract_vbr(f, entry)
				print('=' * 50)

def main():
	parser = build_parser()
	args = parser.parse_args()
	try:
		if not os.path.isfile(args.imagepath):
			raise Exception("The specified file does not exist.")
		run(args)
	except Exception as ex:
		#parser.error(str(ex))
		raise

if __name__ == '__main__':
	main()