from options import Options
import numpy as np
import json
import os
import sys
import subprocess 
import pad
import rulers 
import scipy.misc
import textboxtract
import json2csv
from tqdm import tqdm
# from segmentation.predict import predict

def init_folders(base_folder, mode):
	pdf_folder = os.path.join(base_folder, "pdf", mode)
	if not os.path.exists(pdf_folder):
		os.makedirs(pdf_folder)

	json_folder = os.path.join(base_folder, "json", mode)
	if not os.path.exists(json_folder):
		os.makedirs(json_folder)

	png_folder = os.path.join(base_folder, "png", mode)
	if not os.path.exists(png_folder):
		os.makedirs(png_folder)

	outlines_folder = os.path.join(base_folder, "outlines", mode)
	if not os.path.exists(outlines_folder):
		os.makedirs(outlines_folder)

	results_folder = os.path.join(base_folder, "csv_pred", mode)
	if not os.path.exists(results_folder):
		os.makedirs(results_folder)

	return pdf_folder, json_folder, png_folder, outlines_folder, results_folder

def add_outline_url(json_folder, outline_folder):
	for json_file in os.listdir(json_folder):
		json_file_location = os.path.join(json_folder, json_file)
		with open(json_file_location, 'r+') as jfile:
			result = [] # eventually new json file
			tables = json.load(jfile) # current json file
			for table in tables:
				table["outlineURL"] = os.path.join(outline_folder, os.path.basename(table["renderURL"]))
				result.append(table)
			jfile.seek(0)
			jfile.write(json.dumps(result))
			jfile.truncate()

if __name__ == '__main__':
	opt = Options().parse()
	pdf_folder, json_folder, png_folder, outlines_folder, results_folder = init_folders(opt.dataroot, opt.mode)

	# for pdf in os.listdir(pdf_folder):
	# 	region_boundary = textboxtract.get_region_boundary(os.path.join(pdf_folder, pdf))
	# 	data = [{
	# 		"name": os.path.splitext(pdf)[0],
	# 		"page": 1,
	# 		"dpi": 150,
	# 		"regionBoundary": region_boundary
	# 	}]
	# 	with open(os.path.join(json_folder, os.path.splitext(pdf)[0]+'.json'), 'w') as outfile:
	# 		json.dump(data, outfile)

	# Process the tables, add outline URL to respective JSON file
	if not opt.skip_predict:
		print("Predicting outlines")
		if opt.model == 'pix2pixHD':
			subprocess.call(['python', './pix2pixHD/predict.py', '--name', 'gen-tables', '--checkpoints_dir', opt.checkpoint_dir,  '--dataroot', opt.dataroot, '--loadSize', '1024', '--fineSize', '1024', '--no_instance', '--label_nc', '0', '--results_dir', outlines_folder, '--mode', opt.mode, '--which_epoch', opt.epoch])
		elif opt.model == 'encoder-decoder-skip':
			subprocess.call(['python', './segmentation/bulk_predict.py', '--input_folder', png_folder, '--output_folder', outlines_folder, '--checkpoint_path', opt.checkpoint_dir, '--crop_height', '1024', '--crop_width', '1024', '--model', 'Encoder-Decoder-Skip'])
		else:
			print("Unknown model")
			exit(-1)
	# Interpret ruling lines and write individual cells to json file
	if not opt.skip_find_cells:
		print("Finding cells")
		rulers.rule(json_folder, outlines_folder)

	# Extract the text, using the bounding boxes, from the original PDF
	if not opt.skip_extract_text:
		print("Extracting text")
		textboxtract.extract(json_folder, pdf_folder)

	# Create CSV files from the extracted text and locations of said text
	if not opt.skip_create_csv:
		print("Creating csv")
		json2csv.json2csv(json_folder, results_folder)