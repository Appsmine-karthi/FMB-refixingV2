#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <stack>
#include <iostream>

namespace py = pybind11;

int get_same_pix_count(cv::Mat &a, cv::Mat &b, int &h, int &w)
{
    int counter = 0;
    cv::Vec3b pixel(0, 0, 255);
    for (int y = 0; y < h; y++)
    {
        for (int x = 0; x < w; x++)
        {
            if ((a.at<cv::Vec3b>(y, x) == pixel) && (b.at<cv::Vec3b>(y, x) == pixel))
            {
                counter++;
            }
        }
    }
    return counter;
}

int process(const py::array_t<uint8_t> &pdf, const py::array_t<uint8_t> &wld)
{

    py::buffer_info buf = pdf.request();
    cv::Mat pdf_img(buf.shape[0], buf.shape[1], CV_8UC3, (uint8_t *)buf.ptr);

    buf = wld.request();
    cv::Mat wld_img(buf.shape[0], buf.shape[1], CV_8UC3, (uint8_t *)buf.ptr);

    cv::Size sz = pdf_img.size();

    // std::cout << sz.height << std::endl;
    // std::cout << sz.width << std::endl;

    int normal = 0, flp_x = 0, flp_y = 0, flp_xy = 0;

    normal = get_same_pix_count(pdf_img, wld_img, sz.height, sz.width);

    cv::flip(pdf_img, pdf_img, 0); // flip vertical
    flp_y = get_same_pix_count(pdf_img, wld_img, sz.height, sz.width);

    cv::flip(pdf_img, pdf_img, 1); // flip horizontaly
    flp_xy = get_same_pix_count(pdf_img, wld_img, sz.height, sz.width);

    cv::flip(pdf_img, pdf_img, 0); // flip vertical,horizontal
    flp_x = get_same_pix_count(pdf_img, wld_img, sz.height, sz.width);

    cv::flip(pdf_img, pdf_img, 1);//revert to original

    // std::cout << "normal :" << normal << std::endl;
    // std::cout << "flp_x :" << flp_x << std::endl;
    // std::cout << "flp_y :" << flp_y << std::endl;
    // std::cout << "flp_xy :" << flp_xy << std::endl;

    int bigMatch = std::max({normal,flp_y,flp_xy,flp_x});
    if(bigMatch == normal)
    return -2;
    if(bigMatch == flp_y)
    return 0;
    if(bigMatch == flp_xy)
    return -1;
    if(bigMatch == flp_x)
    return 1;

    return -2;
}

PYBIND11_MODULE(flipMatch, m)
{
    m.doc() = "Image processing module using OpenCV";
    m.def("process", &process, "Process an image and return an int array");
}


/*
To compile this C++ file with pybind11 and OpenCV, use a command similar to:

python 3.12
g++ -O3 -Wall -shared -std=c++14 -fPIC \
    $(python3.12-config --includes) \
    -I$(python3.12 -m pybind11 --includes | cut -c3-) \
    $(pkg-config --cflags opencv4) \
    -o flipMatch$(python3.12-config --extension-suffix) flip.cpp \
    $(python3.12-config --ldflags) \
    $(pkg-config --libs opencv4) -I include

python 3.13
g++ -O3 -Wall -shared -std=c++14 -fPIC \
    $(python3.13-config --includes) \
    -I$(python3.13 -m pybind11 --includes | cut -c3-) \
    $(pkg-config --cflags opencv4) \
    -o flipMatch$(python3.13-config --extension-suffix) flip.cpp \
    $(python3.13-config --ldflags) \
    $(pkg-config --libs opencv4) -I include

Make sure to adjust the paths and Python version if needed.
*/