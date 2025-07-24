#include <pybind11/pybind11.h>
#include <pybind11/numpy.h> 
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <stack>

namespace py = pybind11;

void removeDuplicates(std::vector<int>& vec) {
    std::sort(vec.begin(), vec.end());
    auto last = std::unique(vec.begin(), vec.end());
    vec.erase(last, vec.end());
}

bool verify_pix_q(int x, int y, cv::Mat& img, int x_, int y_, std::vector<int>& line_ind)
{
    if (x > x_ || x < 0 || y > y_ || y < 0)
        return false;

    cv::Vec3b pixel = img.at<cv::Vec3b>(y, x);

        if (img.empty()) {
    throw std::runtime_error("Image is not initialized.");
    }

    if (static_cast<int>(pixel[0]) == 0 && static_cast<int>(pixel[1]) == 0 && static_cast<int>(pixel[2]) == 0)
    {
        img.at<cv::Vec3b>(y, x) = cv::Vec3b(static_cast<int>(pixel[0]), 0, 255);
        return true;
    }

    if(static_cast<int>(pixel[0]) != 0)
    line_ind.push_back(static_cast<int>(pixel[0]));
    return false;


}


void fill_q(int tx, int ty, cv::Mat& img, std::vector<int>& line_ind)
{
    std::stack<std::pair<int, int>> to_visit;
    to_visit.push({ tx, ty });

    int x_ = img.cols - 1;
    int y_ = img.rows - 1;

    while (!to_visit.empty()) {
        std::pair<int, int> current = to_visit.top();
        to_visit.pop();

        int cx = current.first;
        int cy = current.second;

        if (verify_pix_q(cx - 1, cy, img, x_, y_, line_ind))
            to_visit.push({ cx - 1, cy });
        if (verify_pix_q(cx, cy + 1, img, x_, y_, line_ind))
            to_visit.push({ cx, cy + 1 });
        if (verify_pix_q(cx, cy - 1, img, x_, y_, line_ind))
            to_visit.push({ cx, cy - 1 });
        if (verify_pix_q(cx + 1, cy, img, x_, y_, line_ind))
            to_visit.push({ cx + 1, cy });
    }
}




std::vector<int> process(const py::array_t<uint8_t>& input_image,int seed_x,int seed_y) {
    std::vector<int> line_ind;
    py::buffer_info buf = input_image.request();
    cv::Mat image(buf.shape[0], buf.shape[1], CV_8UC3, (uint8_t*)buf.ptr);
    fill_q(seed_x,seed_y,image,line_ind);
    return line_ind;
}

PYBIND11_MODULE(customFloodFill, m) {
    m.doc() = "Image processing module using OpenCV";
    m.def("process", &process, "Process an image and return an int array");
}

/*
To compile this C++ file with pybind11 and OpenCV, use a command similar to:

g++ -O3 -Wall -shared -std=c++14 -fPIC \
    $(python3.12-config --includes) \
    -I$(python3.12 -m pybind11 --includes | cut -c3-) \
    $(pkg-config --cflags opencv4) \
    -o customFloodFill$(python3.12-config --extension-suffix) app.cpp \
    $(python3.12-config --ldflags) \
    $(pkg-config --libs opencv4) -I include

Make sure to adjust the paths and Python version if needed.
*/
