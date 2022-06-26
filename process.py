"""
process.py. Joshua Curtis
"""
import argparse
from lib.vtk_polydata_from_csv import parseTriangleCSV
import logging
import os
from typing import List
from vtk import (
    vtkActor,
    vtkAdaptiveSubdivisionFilter,
    vtkAppendPolyData,
    vtkCleanPolyData,
    vtkDistancePolyDataFilter,
    vtkNamedColors,
    vtkPolyData,
    vtkPolyDataConnectivityFilter,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkScalarBarActor,
)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)


def _render_output(
    polydata, scalar_range: List[float], scalar_bar: vtkScalarBarActor = None
) -> None:
    vtk_poly_data_mapper = vtkPolyDataMapper()
    vtk_poly_data_mapper.SetInputData(polydata)
    vtk_poly_data_mapper.SetScalarRange(scalar_range[0], scalar_range[1])
    vtk_actor = vtkActor()
    vtk_actor.SetMapper(vtk_poly_data_mapper)
    vtk_colors = vtkNamedColors()
    vtk_renderer = vtkRenderer()
    vtk_renderer.SetBackground(vtk_colors.GetColor3d("silver"))
    vtk_render_window = vtkRenderWindow()
    vtk_render_window.SetSize(640, 480)
    vtk_render_window.AddRenderer(vtk_renderer)
    vtk_render_interactor = vtkRenderWindowInteractor()
    vtk_render_interactor.SetRenderWindow(vtk_render_window)
    vtk_renderer.AddActor(vtk_actor)
    if scalar_bar:
        scalar_bar.SetLookupTable(vtk_poly_data_mapper.GetLookupTable())
        vtk_renderer.AddActor2D(scalar_bar)

    vtk_render_interactor.Initialize()
    vtk_renderer.ResetCamera()
    vtk_render_window.Render()
    vtk_render_interactor.Start()


def main():
    """
    Initiates process from given file input.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("in_file", help="input file containing csv verts")
    parser.add_argument(
        "-t",
        "--tolerance",
        help="tolerance to apply poly data cleanup",
        default=1e-6,
        type=float,
    )

    parser.add_argument(
        "-d", "--distance", help="calculate and render distance", action="store_true"
    )
    args = parser.parse_args()

    # read input data
    vtk_poly_data = parseTriangleCSV(args.in_file)
    logger.info(f"Extracted poly data {vtk_poly_data}")

    # remove duplicate verts
    vtk_clean_poly_data = vtkCleanPolyData()
    vtk_clean_poly_data.SetInputData(vtk_poly_data)
    vtk_clean_poly_data.SetTolerance(args.tolerance)
    vtk_clean_poly_data.Update()
    logger.info(f"Cleaned poly data to join duplicate vertices {vtk_clean_poly_data}")

    # segment surfaces
    vtk_connectivity_filter = vtkPolyDataConnectivityFilter()
    vtk_connectivity_filter.SetInputData(vtk_clean_poly_data.GetOutput())
    vtk_connectivity_filter.SetExtractionModeToAllRegions()
    vtk_connectivity_filter.ColorRegionsOn()
    vtk_connectivity_filter.Update()
    logger.info(f"Joined connected meshes {vtk_connectivity_filter}")

    if not args.distance:
        _render_output(
            vtk_connectivity_filter.GetOutput(),
            vtk_connectivity_filter.GetOutput()
            .GetPointData()
            .GetArray("RegionId")
            .GetRange(),
        )
    else:
        # compute distances
        vtk_append_poly_data = vtkAppendPolyData()
        for i in range(vtk_connectivity_filter.GetNumberOfExtractedRegions()):
            vtk_connectivity_filter.SetExtractionModeToSpecifiedRegions()
            vtk_connectivity_filter.InitializeSpecifiedRegionList()
            vtk_connectivity_filter.AddSpecifiedRegion(i)
            vtk_connectivity_filter.Update()

            vtk_subdivided_data = vtkAdaptiveSubdivisionFilter()
            vtk_subdivided_data.SetInputData(vtk_connectivity_filter.GetOutput())
            vtk_subdivided_data.Update()

            vtk_distance_filter = vtkDistancePolyDataFilter()
            vtk_distance_filter.SignedDistanceOff()
            vtk_distance_filter.ComputeCellCenterDistanceOff()
            vtk_distance_filter.ComputeSecondDistanceOff()
            vtk_distance_filter.SetInputData(0, vtk_subdivided_data.GetOutput())
            vtk_connectivity_filter.InitializeSpecifiedRegionList()

            for j in range(vtk_connectivity_filter.GetNumberOfExtractedRegions()):
                if i == j:
                    continue

                vtk_connectivity_filter.AddSpecifiedRegion(j)

            vtk_connectivity_filter.Update()
            vtk_p2 = vtkPolyData()
            vtk_p2.DeepCopy(vtk_connectivity_filter.GetOutput())
            vtk_distance_filter.SetInputData(1, vtk_p2)
            vtk_distance_filter.Update()

            vtk_append_poly_data.AddInputData(vtk_distance_filter.GetOutput())

        vtk_append_poly_data.Update()
        vtk_scalar_bar = vtkScalarBarActor()
        vtk_scalar_bar.SetTitle("Distance")
        vtk_scalar_bar.SetNumberOfLabels(4)
        vtk_scalar_bar.UnconstrainedFontSizeOn()

        _render_output(
            vtk_append_poly_data.GetOutput(),
            vtk_append_poly_data.GetOutput().GetPointData().GetScalars().GetRange(),
            vtk_scalar_bar,
        )


if __name__ == "__main__":
    main()
