#!/usr/bin/python3

'''A utility for MAC Conversions.
CSE 469 Course Project
'''

import argparse
import binascii

months = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
		  7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}

def build_parser():
	parser = argparse.ArgumentParser(add_help=False)
	parser.add_argument('--help', action='help')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('-T', '--time', action='store_true',
		help='Use time conversion module.  Either -f or -h must be given.')
	group.add_argument('-D', '--date', action='store_true',
		help='Use date conversion module.  Either -f or -h must be given.')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('-f', '--file', metavar='filename',
		help='This specifies the path to a filename that includes a hex value of time or date. Note that the hex value should follow this notation: 0x1234. For the multiple hex values in either a file or a command line input, we consider only one hex value so the recursive mode for MAC conversion is optional.')
	group.add_argument('-h', '--hex', metavar='hex value', type=lambda s: int(s, 16),
		help='This specifies the hex value for converting to either date or time value. Note that the hex value should follow this notation: Ox1234. For the multiple hex values in either a file or a command line input, we consider only one hex value so the recursive mode for MAC conversion is optional.')
	return parser

def convert(args):
	if args.file is not None:
		with open(args.file, 'r') as f:
			data = int(f.read(), 16)

	elif args.hex is not None:
	   data = args.hex

	else:
		raise Exception('Either arguments -f or -h must be provided.')

	data = convertLittleEndian(data)
	if args.time:
		print(parseTime(data))

	elif args.date:
		print(parseDate(data))

	else:
		raise Exception('Either arguments -T or -D must be provided.')
			   
def parseDate(number):
	month = months[(number>>5) & 0xf]
	day = number & 0x1f
	year = ((number >> 9) & 0x7f) + 1980

	return 'Date: {0} {1}, {2}'.format(month, day, year) 

def parseTime(number):
	ampm = 'AM'
	seconds = (number & 0x1f) * 2
	minutes = (number >> 5) & 0x3f
	hours = (number >> 11) & 0x1f
	if (hours > 12):
		hours = hours-12
		ampm = 'PM'
	return 'Time: {0}:{1}:{2} {3}'.format(hours, minutes, seconds, ampm) 

def convertLittleEndian(number):
	return (number >> 8) | ((number & 0xff) << 8) 

def main():
	parser = build_parser()
	args = parser.parse_args()
	try:
		convert(args)
	except Exception as ex:
		parser.error(str(ex))

if __name__ == '__main__':
	main()
