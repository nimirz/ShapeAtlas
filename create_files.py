#!/usr/bin/env python3
# USAGE
# python create_files.py [--config configfile]

from pathlib import Path
import argparse
import csv
import yaml
import os

def write_data_set_xml(root_directory, parameters):
    list_vtk = list(root_directory.glob('*_a.vtk'))
    list_vtk.sort()
    file = open(root_directory / "data_set.xml", "w")
    file.write("<?xml version=\"1.0\"?>\n")
    file.write("<data-set>\n")
    for vtk_file, indice in zip(list_vtk, range(len(list_vtk))):
        if vtk_file.name != 'initial_template.vtk':
            file.write("    <subject id=\"%s\">\n" %vtk_file.name.split('_')[0])
            file.write("        <visit id=\"experiment\">\n")
            file.write("            <filename object_id=\"%s\">%s</filename>\n" % (parameters['object_id'],
                                                                                    vtk_file.name))
            file.write("        </visit>\n")
            file.write("    </subject>\n")
    file.write("</data-set>\n")
    file.close()


def write_model_xml(root_directory, parameters):
    file = open(root_directory / "model.xml", "w")
    file.write("<?xml version=\"1.0\"?>\n")
    file.write("<model>\n")
    file.write("    <model-type>%s</model-type>\n" % parameters['model_type'])
    file.write("    <dimension>3</dimension>\n")
    file.write("    <template>\n")
    file.write("        <object id=\"%s\">\n" % parameters['object_id'])
    file.write("            <deformable-object-type>%s</deformable-object-type>\n" % parameters['object_type'])
    file.write("	    <attachment-type>%s</attachment-type>\n" % parameters['attachment_type'])
    file.write("            <noise-std>%s</noise-std>\n" % parameters['noise_std'])
    file.write("            <kernel-type>keops</kernel-type>\n")
    file.write("            <kernel-width>%s</kernel-width>\n" % parameters['object_kernel_width'])
    file.write("            <filename>initial_template.vtk</filename>\n")
    file.write("        </object>\n")
    file.write("    </template>\n")
    file.write("    <deformation-parameters>\n")
    file.write("        <kernel-width>%s</kernel-width>\n" % parameters['deformation_kernel_width'])
    file.write("        <kernel-type>keops</kernel-type>\n")
    file.write("        <number-of-timepoints>20</number-of-timepoints>\n")
    file.write("    </deformation-parameters>\n")
    file.write(" </model>\n")
    file.close()


def write_optimization_parameters_xml(root_directory, parameters):
    file = open(root_directory / "optimization_parameters.xml", "w")
    file.write("<?xml version=\"1.0\"?>\n")
    file.write("<optimization-parameters>\n")
    file.write("    <optimization-method-type>GradientAscent</optimization-method-type>\n" )
    file.write("    <initial-step-size>%s</initial-step-size>\n" % parameters['initial_step_size'])
    file.write("    <max-iterations>%s</max-iterations>\n" % parameters['max_iterations'])
    file.write("    <convergence-tolerance>%s</convergence-tolerance>\n" % parameters['convergence_tolerance'])
    file.write("    <freeze-template>%s</freeze-template>\n" % parameters['freeze_template'])
    file.write("    <freeze-control-points>%s</freeze-control-points>\n" % parameters['freeze_control_points'])
    file.write("</optimization-parameters>\n")
    file.close()


def main():
    # construct argument parse and parse arguments
    parser = argparse.ArgumentParser(description='Create xml files to run model.')
    parser.add_argument('--config', help='Path to config file', default='configs/mesh.yaml')
    args = parser.parse_args()

    # load config
    print(f'Using config "{args.config}"')
    cfg = yaml.safe_load(open(args.config, 'r'))

    direc = cfg['root'] + '/model_runs/' + cfg['expname'] + '/'
    os.makedirs(direc, exist_ok = True)
    paramfile = cfg['root'] + 'parameters.csv'

    with open(paramfile, "r") as infile:
        reader = list(csv.DictReader(infile))
    
    for dic in reader:
        if dic['expname'] == cfg['expname']:
            paramDict = dic

            
    write_data_set_xml(Path(direc), paramDict)
    write_model_xml(Path(direc), paramDict)
    write_optimization_parameters_xml(Path(direc), paramDict)

if __name__ == '__main__':
    main()