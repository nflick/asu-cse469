#!/usr/bin/env python

'''A utility for converting between various hard disk address representations.
CSE 469 Course Project
'''

import argparse

def build_parser():
	parser = argparse.ArgumentParser()
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('-L', '--logical', action='store_true',
		help='Calculate the logical address from either the cluster address or the physical address. Either –c or –p must be given.')
	group.add_argument('-P', '--physical', action='store_true',
		help='Calculate the physical address from either the cluster address or the logical address. Either -c or -l must be given.')
	group.add_argument('-C', '--cluster', action='store_true',
		help='Calculate the cluster address from either the logical address or the physical address. Either -l or -p must be given.')
	parser.add_argument('-b', '--partition-start', metavar='offset', type=int, default=0,
		help='This specifies the physical address (sector number) of the start of the partition, and defaults to 0 for ease in working with images of a single partition. The offset value will always translate into logical address 0.')
	parser.add_argument('-B', '--byte-address', action='store_true',
		help='Instead of returning sector values for the conversion, this returns the byte address of the calculated value, which is the number of sectors multiplied by the number of bytes per sector.')
	parser.add_argument('-s', '--sector-size', metavar='bytes', type=int,
		help='When the -B option is used, this allows for a specification of bytes per sector other than the default 512. Has no affect on output without -B.')
	parser.add_argument('-l', '--logical-known', metavar='address', type=int,
		help='This specifies the known logical address for calculating either a cluster address or a physical address. When used with the -L option, this simply returns the value giben for address.')
	parser.add_argument('-p', '--physical-known', metavar='address', type=int,
		help='This specifies the known physical address for calculating either a cluster address or a logical address. When used with the -P option, this simply returns the value given for address.')
	parser.add_argument('-c', '--cluster-known', metavar='address', type=int,
		help='This speficies the known cluster address for calculating either a logical address or a physical address. When used with the -C option, this simply return the value given for address. Note that options -k, -r, -t, and -f must be provided with this option')
	parser.add_argument('-k', '--cluster-size', metavar='sectors', type=int,
		help='This specifies the number of sectors per cluster.')
	parser.add_argument('-r', '--reserved', metavar='sectors', type=int,
		help='This specifies the number of reserved sectors in the partition.')
	parser.add_argument('-t', '--fat-tables', metavar='tables', type=int,
		help='This specifies the number of FAT tables, which is usually 2.')
	parser.add_argument('-f', '--fat-length', metavar='sectors', type=int,
		help='This specifies the length of each FAT table in sectors.')
	return parser

def convert(args):
	# The known address is converted to a physical address and then to the target address type.
	physical = None
	if args.logical_known:
		physical =  args.partition_start + args.logical_known
	if args.physical_known:
		physical = args.physical_known
	if args.cluster_known:
		if args.cluster_size is None or args.reserved is None or args.fat_tables is None or args.fat_length is None:
			raise Exception('-k, -r, -t, and -f must be provided with -c.')
		physical = args.partition_start + args.reserved + args.fat_tables * args.fat_length + (args.cluster_known - 2) * args.cluster_size
	# If physical is still none, it means no known address was provided
	if physical is None:
		raise Exception('at least one of -l, -p, or -c must be provided.')

	converted = None
	# The argument parser enforces that one of the following options is selected.
	if args.logical:
		converted = physical - args.partition_start
	if args.physical:
		converted = physical
	if args.cluster:
		converted = (physical - (args.partition_start + args.reserved + args.fat_tables * args.fat_length)) // args.cluster_size + 2

	# Check if output should be in bytes instead of sectors.
	if args.byte_address:
		# Conflicts with output in clusters
		if args.cluster:
			raise Exception('-B is invalid when using -C.')
		converted *= args.sector_size

	print(converted)


def main():
	parser = build_parser()
	args = parser.parse_args()
	try:
		convert(args)
	except Exception as ex:
		parser.error(str(ex))

if __name__ == '__main__':
	main()