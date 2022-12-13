
'''
    Script for aligning mesh files labeled MITK landmark points.
    Mesh files shoudl be VTK files and in 'data/mesh' and landmark files
    should be in 'data/landmarks'. Output mesh will be saved in 'experiments/expname'
    Experiment name is specified in config file.

'''

import os
from glob import glob
import argparse

# read LMS file
def read_mps_file(landmarksfile):
    """Read MPS file (from [MITK](http://mitk.org/wiki/The_Medical_Imaging_Interaction_Toolkit_(MITK)))
        Converts the XML landmarks into a Numpy array
    """
    ### import XML reader
    import xml.etree.ElementTree as ET
    import numpy as np
    ### read file
    tree = ET.parse(landmarksfile)
    root = tree.getroot()
    ### list elements which tags are 'point'
    point_elements = [elem for elem in root.iter() if (elem is not root) and (elem.tag == 'point')]
    ### feed the numpy array
    lms = np.zeros([len(point_elements), 3])
    for idx, p in enumerate(point_elements):
        lms[idx, 0] = float(p.find('x').text)
        lms[idx, 1] = float(p.find('y').text)
        lms[idx, 2] = float(p.find('z').text)
    return lms


def numpy_landmarks_to_vtk(numpy_landmarks_array):
    import vtk

    landmarksgroup = vtk.vtkMultiBlockDataGroupFilter()
    for landmarks in numpy_landmarks_array:
        pts = vtk.vtkPoints()
        for landmark in landmarks:
            pts.InsertNextPoint(landmark[0], landmark[1], landmark[2])
        poly = vtk.vtkPolyData()
        poly.SetPoints(pts)
        landmarksgroup.AddInputData(poly)
    return landmarksgroup


def vtk_to_numpy_landmarks(vtk_multiblock_dataset):
    import numpy as np

    number_of_landmarksets = vtk_multiblock_dataset.GetNumberOfBlocks()
    number_of_landmarks = vtk_multiblock_dataset.GetBlock(0).GetNumberOfPoints()
    landmarks = np.zeros([number_of_landmarksets, number_of_landmarks, 3])
    for id1 in range(number_of_landmarksets):
        for id2 in range(number_of_landmarks):
            l = vtk_multiblock_dataset.GetBlock(id1).GetPoint(id2)
            landmarks[id1, id2] = l
    return landmarks


def centroid(vtk_points):

    cp = [0] * 3
    np = vtk_points.GetNumberOfPoints()
    for i in range(np):
        p = vtk_points.GetPoint(i)
        cp[0] += p[0]; cp[1] += p[1]; cp[2] += p[2];
    cp[0] /= np; cp[1] /= np; cp[2] /= np;
    return cp


def centroid_size(vtk_points):
    import vtk
    import numpy as np

    cp = centroid(vtk_points)
    n = vtk_points.GetNumberOfPoints()
    S = 0
    for i in range(n):
        p = vtk_points.GetPoint(i)
        S += vtk.vtkMath.Distance2BetweenPoints(p, cp)
    return np.sqrt(S)


def scale_shape(vtk_points, factor):
    import vtk
    import numpy as np

    np = vtk_points.GetNumberOfPoints()
    for i in range(np):
        p = vtk_points.GetPoint(i)
        vtk_points.SetPoint(i, p[0] * factor, p[1] * factor, p[2] * factor)
    return


def execute_procrustes(vtk_landmark_group, mode='similarity'):
    import vtk
    import numpy as np

    # compute the Procrustes from all landmark files
    procrustes = vtk.vtkProcrustesAlignmentFilter()
    procrustes.SetInputConnection(vtk_landmark_group.GetOutputPort())
    if mode == 'similarity':
        procrustes.GetLandmarkTransform().SetModeToSimilarity()
    elif mode == 'rigid':
        procrustes.GetLandmarkTransform().SetModeToRigidBody()
    elif mode == 'affine':
        procrustes.GetLandmarkTransform().SetModeToAffine()
    procrustes.Update()

    ret_dataset = procrustes.GetOutput()
    ret_mean_points = procrustes.GetMeanPoints()

    if mode == 'similarity':
        S = np.array([centroid_size(vtk_landmark_group.GetOutput().GetBlock(idx)) for idx in
                      range(vtk_landmark_group.GetOutput().GetNumberOfBlocks())])
        s = np.mean(S)
        scale_shape(ret_mean_points, s)

        for idx in range(vtk_landmark_group.GetOutput().GetNumberOfBlocks()):
            scale_shape(ret_dataset.GetBlock(idx).GetPoints(), s)

    return ret_dataset, ret_mean_points


def align_meshes_to_center(meshfiles, landmarksfiles, mode='similarity', output_directory=None, suffix='_r'):
    import os
    import vtk
    import numpy as np

    if output_directory is None:
        output_directory = os.getcwd()

    numpy_landmarks = np.array([read_mps_file(l) for l in landmarksfiles])
    vtk_landmarks_group = numpy_landmarks_to_vtk(numpy_landmarks)


    procrustes_output, procrustes_mean_points = execute_procrustes(vtk_landmarks_group, mode=mode)

    output_meshes = []
    ### iterate over the mesh / landmarks pairs
    for idx, (m, l) in enumerate(zip(meshfiles, landmarksfiles)):

        ### read mesh
        reader = vtk.vtkPolyDataReader()
        reader.SetFileName(m)
        reader.Update()
        mesh = reader.GetOutput()

        ### read landmarks
        lms = read_mps_file(l)
        sourcepoints = vtk.vtkPoints()
        for p in lms:
            sourcepoints.InsertNextPoint(p[0], p[1], p[2])

        ### recover the aligned landmarks (to the mean)
        targetpoints = procrustes_output.GetBlock(idx).GetPoints()

        ### create a transform filter to move input mesh towards the center
        transform = vtk.vtkLandmarkTransform()
        transform.SetSourceLandmarks(sourcepoints)
        transform.SetTargetLandmarks(targetpoints)

        if mode == 'similarity':
            transform.SetModeToSimilarity()
        elif mode == 'rigid':
            transform.SetModeToRigidBody()
        elif mode == 'affine':
            transform.SetModeToAffine()
        transform.Update()

        transformedpoints = vtk.vtkPoints()
        transform.TransformPoints(mesh.GetPoints(), transformedpoints)
        mesh.SetPoints(transformedpoints)

        ### save moved mesh to input_file_r.vtk
        fn, _ = os.path.splitext(os.path.basename(m))
        w = vtk.vtkPolyDataWriter()
        ofilename = '{}{}{}{}.vtk'.format(output_directory, os.sep, fn, suffix)
        w.SetFileName(ofilename)
        w.SetInputData(mesh)
        w.Update()
        output_meshes.append(ofilename)

        print('moving {} towards center with landmarks {} -- determinant: {:.2f}'.format(os.path.basename(m),
                                                                                         os.path.basename(l),
                                                                                         transform.GetMatrix().Determinant()))

    return output_meshes



def main():
    meshfolder = 'data/mesh/unaligned/'
    landfolder = 'data/landmarks/'
    outdir = 'data/mesh/aligned/'
    os.makedirs(outdir, exist_ok=True)

    # get mesh and landmark files    
    meshFiles = glob('{}*.vtk'.format(meshfolder))
    landmarkFiles = glob('{}{}*.mps'.format(landfolder, os.sep))
    # ignore initial template or already aligned files
    meshFiles[:] = [el for el in meshFiles if not (('initial_template.vtk' in el) or ('_a.vtk' in el)) ]

    # assert similar size and sort lists
    print("Number of meshfiles {}".format(len(meshFiles)))
    print("Number of landmark files: {}".format(len(landmarkFiles)))
    assert(len(meshFiles) == len(landmarkFiles))
    meshFiles.sort()
    landmarkFiles.sort()

    align_meshes_to_center(meshFiles, landmarkFiles, mode="similarity", 
                            output_directory=outdir, suffix='_a')


if __name__ == '__main__':
    main()