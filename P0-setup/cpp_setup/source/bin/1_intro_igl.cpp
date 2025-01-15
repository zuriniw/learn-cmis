#include <igl/readOBJ.h>
#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/imgui/ImGuiMenu.h>
#include <igl/opengl/glfw/imgui/ImGuiHelpers.h>
#include <imgui/imgui.h>

#include <iostream>

#include "model_path.h"


int main(int argc, char* argv[]) {
    Eigen::MatrixXd V;
    Eigen::MatrixXi F;

    // Read mesh
    igl::readOBJ(PathHelper::get_folder_path(__FILE__) + "/../../models/bunny.obj", V, F);

    // Create a viewer
    igl::opengl::glfw::Viewer viewer;
    viewer.core().background_color.setOnes();

    // Add the mesh to the viewer
    viewer.data().set_mesh(V, F);

    // Create a color matrix with one RGB color per vertex
    Eigen::MatrixXd C(V.rows(), 3);
    C.col(0).fill(0.0); // Red channel
    C.col(1).fill(1.0); // Green channel
    C.col(2).fill(0.0); // Blue channel

    // Set the colors of the mesh vertices
    viewer.data().set_colors(C);

    // Launch the viewer
    viewer.launch();
}
