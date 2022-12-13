#!/usr/bin/env python3
'''
This file converts ply or stl files to vtk files, or vtk files to ply

To use, specify the input folder via the -i flag and the filetype to convert via the -t flag.

Usage:
python convert.py -i inputfolder -t filetype

'''

# load packages
import pyvista as pv
import argparse
from glob import glob
import os

def main():
	ap = argparse.ArgumentParser(description='Covert mesh files from ply or stl to vtk.')
	ap.add_argument("-i", "--input", required=True, help="Path to directory with mesh files.")
	ap.add_argument("-t", "--type", required=True, help="Type of files to convert.")
	args = vars(ap.parse_args())

	ext = args["type"]
	directory = args["input"]
	files = glob('{}{}*{}'.format(directory, os.sep, ext))

	if not files:
		print('No {} files in folder!'.format(ext))
		exit()

	for file in files:
		m = pv.read(file)
		fn, extension = os.path.splitext(file)
		if extension == '.vtk':
			m.save(fn + '.ply')
		elif extension == '.stl':
			m.save(fn + '.vtk')
		elif extension == '.ply': 
			m.save(fn + '.vtk')
		
	print('Total of {} {} files converted'.format(len(files), ext))

if __name__ == '__main__':
    main()