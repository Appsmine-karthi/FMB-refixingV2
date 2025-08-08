#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <stack>
#include <iostream>

namespace py = pybind11;

int get_same_pix_count(cv::Mat &a, cv::Mat &b, int &h, int &w, cv::Vec3b target_pixel = cv::Vec3b(0, 0, 255))
{
    int counter = 0;
    for (int y = 0; y < h; y++)
    {
        for (int x = 0; x < w; x++)
        {
            if ((a.at<cv::Vec3b>(y, x) == target_pixel) && (b.at<cv::Vec3b>(y, x) == target_pixel))
            {
                counter++;
            }
        }
    }
    return counter;
}

void create_overlay_image(cv::Mat &pdf_img, cv::Mat &wld_img, const std::string &filename, bool debug_output = false)
{
    if (!debug_output) return;
    
    // Create overlay image
    cv::Mat overlay = cv::Mat::zeros(pdf_img.size(), CV_8UC3);
    
    // Convert images to different colors for visualization
    cv::Mat pdf_blue, wld_red;
    
    // PDF image in blue (BGR: 255, 0, 0)
    cv::cvtColor(pdf_img, pdf_blue, cv::COLOR_BGR2GRAY);
    cv::cvtColor(pdf_blue, pdf_blue, cv::COLOR_GRAY2BGR);
    pdf_blue.setTo(cv::Scalar(255, 0, 0), pdf_img == cv::Vec3b(0, 0, 255)); // Red pixels become blue
    
    // WLD image in red (BGR: 0, 0, 255)
    cv::cvtColor(wld_img, wld_red, cv::COLOR_BGR2GRAY);
    cv::cvtColor(wld_red, wld_red, cv::COLOR_GRAY2BGR);
    wld_red.setTo(cv::Scalar(0, 0, 255), wld_img == cv::Vec3b(0, 0, 255)); // Red pixels stay red
    
    // Combine images
    cv::addWeighted(pdf_blue, 0.7, wld_red, 0.7, 0, overlay);
    
    // Add text labels
    cv::putText(overlay, "PDF (Blue)", cv::Point(10, 30), cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(255, 0, 0), 2);
    cv::putText(overlay, "WLD (Red)", cv::Point(10, 60), cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(0, 0, 255), 2);
    cv::putText(overlay, "Overlap (Purple)", cv::Point(10, 90), cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(255, 0, 255), 2);
    
    cv::imwrite(filename, overlay);
}

int process(const py::array_t<uint8_t> &pdf, const py::array_t<uint8_t> &wld, bool debug_output = false)
{
    // Input validation
    py::buffer_info buf_pdf = pdf.request();
    py::buffer_info buf_wld = wld.request();
    
    if (buf_pdf.ndim != 3 || buf_wld.ndim != 3) {
        throw std::runtime_error("Input images must be 3D arrays (height, width, channels)");
    }
    
    if (buf_pdf.shape[0] != buf_wld.shape[0] || buf_pdf.shape[1] != buf_wld.shape[1]) {
        throw std::runtime_error("Input images must have the same dimensions");
    }

    cv::Mat pdf_img(buf_pdf.shape[0], buf_pdf.shape[1], CV_8UC3, (uint8_t *)buf_pdf.ptr);
    cv::Mat wld_img(buf_wld.shape[0], buf_wld.shape[1], CV_8UC3, (uint8_t *)buf_wld.ptr);
    cv::Size sz = pdf_img.size();

    // Create a working copy to avoid modifying original
    cv::Mat working_img = pdf_img.clone();

    // Test all orientations: 0°, 90°, 180°, 270° rotations with flips
    int normal = 0, flp_x = 0, flp_y = 0, flp_xy = 0;
    int flp_x_90 = 0, flp_y_90 = 0, flp_xy_90 = 0;
    int flp_x_180 = 0, flp_y_180 = 0, flp_xy_180 = 0;
    int flp_x_270 = 0, flp_y_270 = 0, flp_xy_270 = 0;

    // 0° rotation cases
    normal = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_normal.png", debug_output);
    if (debug_output) cv::imwrite("normal.png", working_img);

    cv::flip(working_img, working_img, 0); // flip vertical
    flp_y = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_y.png", debug_output);
    if (debug_output) cv::imwrite("flp_y.png", working_img);
    
    cv::flip(working_img, working_img, 1); // flip vertical,horizontal
    flp_xy = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_xy.png", debug_output);
    if (debug_output) cv::imwrite("flp_xy.png", working_img);
    
    cv::flip(working_img, working_img, 0); // flip horizontal
    flp_x = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_x.png", debug_output);
    if (debug_output) cv::imwrite("flp_x.png", working_img);
    
    cv::flip(working_img, working_img, 1); // revert to original
    if (debug_output) cv::imwrite("normal.png", working_img);

    // 90° rotation cases
    cv::Point2f center(working_img.cols / 2.0F, working_img.rows / 2.0F);
    cv::Mat rot = cv::getRotationMatrix2D(center, 90, 1.0);
    cv::warpAffine(working_img, working_img, rot, working_img.size(), cv::INTER_LINEAR, cv::BORDER_CONSTANT, cv::Scalar(0,0,0));
    
    flp_y_90 = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_y_90.png", debug_output);
    if (debug_output) cv::imwrite("flp_y_90.png", working_img);
    
    cv::flip(working_img, working_img, 1); // flip vertical,horizontal
    flp_xy_90 = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_xy_90.png", debug_output);
    if (debug_output) cv::imwrite("flp_xy_90.png", working_img);
    
    cv::flip(working_img, working_img, 0); // flip horizontal
    flp_x_90 = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_x_90.png", debug_output);
    if (debug_output) cv::imwrite("flp_x_90.png", working_img);
    
    cv::flip(working_img, working_img, 1); // revert to 90° rotation
    if (debug_output) cv::imwrite("rot_90.png", working_img);

    // 180° rotation cases (rotate 90° again from 90° position)
    rot = cv::getRotationMatrix2D(center, 90, 1.0);
    cv::warpAffine(working_img, working_img, rot, working_img.size(), cv::INTER_LINEAR, cv::BORDER_CONSTANT, cv::Scalar(0,0,0));
    
    flp_y_180 = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_y_180.png", debug_output);
    if (debug_output) cv::imwrite("flp_y_180.png", working_img);
    
    cv::flip(working_img, working_img, 1); // flip vertical,horizontal
    flp_xy_180 = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_xy_180.png", debug_output);
    if (debug_output) cv::imwrite("flp_xy_180.png", working_img);
    
    cv::flip(working_img, working_img, 0); // flip horizontal
    flp_x_180 = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_x_180.png", debug_output);
    if (debug_output) cv::imwrite("flp_x_180.png", working_img);
    
    cv::flip(working_img, working_img, 1); // revert to 180° rotation
    if (debug_output) cv::imwrite("rot_180.png", working_img);

    // 270° rotation cases (rotate 90° again from 180° position)
    rot = cv::getRotationMatrix2D(center, 90, 1.0);
    cv::warpAffine(working_img, working_img, rot, working_img.size(), cv::INTER_LINEAR, cv::BORDER_CONSTANT, cv::Scalar(0,0,0));
    
    flp_y_270 = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_y_270.png", debug_output);
    if (debug_output) cv::imwrite("flp_y_270.png", working_img);
    
    cv::flip(working_img, working_img, 1); // flip vertical,horizontal
    flp_xy_270 = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_xy_270.png", debug_output);
    if (debug_output) cv::imwrite("flp_xy_270.png", working_img);
    
    cv::flip(working_img, working_img, 0); // flip horizontal
    flp_x_270 = get_same_pix_count(working_img, wld_img, sz.height, sz.width);
    create_overlay_image(working_img, wld_img, "overlay_flp_x_270.png", debug_output);
    if (debug_output) cv::imwrite("flp_x_270.png", working_img);

    // Find the best match
    int bigMatch = std::max({normal, flp_y, flp_xy, flp_x, 
                           flp_y_90, flp_xy_90, flp_x_90, 
                           flp_y_180, flp_xy_180, flp_x_180, 
                           flp_y_270, flp_xy_270, flp_x_270});
    
    // Return codes:
    // -2: no match found (normal orientation is best)
    // 0-3: 0° rotation with different flips
    // 10-13: 90° rotation with different flips  
    // 20-23: 180° rotation with different flips
    // 30-33: 270° rotation with different flips

    // Print all cases and their match values
    std::cout << "normal: " << normal << std::endl;
    std::cout << "flp_y: " << flp_y << std::endl;
    std::cout << "flp_xy: " << flp_xy << std::endl;
    std::cout << "flp_x: " << flp_x << std::endl;
    std::cout << "flp_y_90: " << flp_y_90 << std::endl;
    std::cout << "flp_xy_90: " << flp_xy_90 << std::endl;
    std::cout << "flp_x_90: " << flp_x_90 << std::endl;
    std::cout << "flp_y_180: " << flp_y_180 << std::endl;
    std::cout << "flp_xy_180: " << flp_xy_180 << std::endl;
    std::cout << "flp_x_180: " << flp_x_180 << std::endl;
    std::cout << "flp_y_270: " << flp_y_270 << std::endl;
    std::cout << "flp_xy_270: " << flp_xy_270 << std::endl;
    std::cout << "flp_x_270: " << flp_x_270 << std::endl;
    
    if (bigMatch == normal)
        return -2;

    // 0° rotation cases
    if (bigMatch == flp_y)
        return 0;
    if (bigMatch == flp_xy)
        return 1;
    if (bigMatch == flp_x)
        return 1;

    // 90° rotation cases
    if (bigMatch == flp_y_90)
        return 10;
    if (bigMatch == flp_xy_90)
        return 11;
    if (bigMatch == flp_x_90)
        return 12;

    // 180° rotation cases
    if (bigMatch == flp_y_180)
        return 20;
    if (bigMatch == flp_xy_180)
        return 21;
    if (bigMatch == flp_x_180)
        return 22;

    // 270° rotation cases
    if (bigMatch == flp_y_270)
        return 30;
    if (bigMatch == flp_xy_270)
        return 31;
    if (bigMatch == flp_x_270)
        return 32;

    return -2;
}

PYBIND11_MODULE(flipMatch, m)
{
    m.doc() = "Image processing module using OpenCV";
    m.def("process", &process, py::arg("pdf"), py::arg("wld"), py::arg("debug_output") = false, 
          "Process an image and return orientation code. debug_output controls whether to save debug images.");
}