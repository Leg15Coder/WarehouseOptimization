#include"input_stuff.cpp"
#include"pathfinder.cpp"
#include"fancy_output.cpp"

#include<iostream>

int maxcoord = 100;

point scale(point pt, int mult) {
    return {pt.first * mult, pt.second * mult};
}

int dot_width = 20;

void print_fancy(std::string name, const path& pth) {
    bmp image(name, maxcoord*dot_width, maxcoord*dot_width);
    for(int i = 0; i + 1 < pth.size(); i++)
        image.draw_line(scale(pth[i], dot_width), scale(pth[i + 1], dot_width), 5, 0xff000000);
    image.draw_line(scale(pth[0], dot_width), scale(pth[0], dot_width), dot_width, 0xff880000);
    for(int i = 1; i < pth.size(); i++)
        image.draw_line(scale(pth[i], dot_width), scale(pth[i], dot_width), dot_width, 0xff000088);
    image.save();
}

int main() {
    if(0) random_input(100, 100, maxcoord);
    input inp = read_from_file();
    print_fancy("before.bmp", inp.points_);
    Otjig().optimise(&inp.points_, 10000000);
    print_fancy("after.bmp", inp.points_);
}