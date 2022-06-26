"""
Vert file parser that provides a collection triangles from a csv file.
"""
import numpy as np
from vtk import vtkPolyData, vtkPoints, vtkCellArray, vtkTriangle
import vtk.util.numpy_support as npsup


def parseTriangleCSV(in_file: str) -> vtkPolyData:
    """
    Helper function for parsing triangles contained in a csv file.
    Each line of the file represents a triangle in ASCII CSV format using 9 floating point numbers to represent the three vertices of the triangle as x0, y0, z0, x1, y1, z1, x2, y2, z2.
    """
    triangles = np.loadtxt(in_file, delimiter=",")
    vertices = np.reshape(triangles, (-1, 3))

    vtk_points = vtkPoints()
    vtk_points.SetData(npsup.numpy_to_vtk(vertices, deep=True))
    vtk_cell_array = vtkCellArray()
    for i, _ in enumerate(triangles):
        vtk_triangle = vtkTriangle()
        vtk_triangle.GetPointIds().SetId(0, i * 3 + 0)
        vtk_triangle.GetPointIds().SetId(1, i * 3 + 1)
        vtk_triangle.GetPointIds().SetId(2, i * 3 + 2)
        vtk_cell_array.InsertNextCell(vtk_triangle)

    polydata = vtkPolyData()
    polydata.SetPoints(vtk_points)
    polydata.SetPolys(vtk_cell_array)
    polydata.Modified()

    return polydata
