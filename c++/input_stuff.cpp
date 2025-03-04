#pragma once

#include<fstream>
#include<random>

std::string in_path = "./in.txt";
std::string out_path = "./out.txt";

using point = std::pair<int, int>;
std::istream& operator>>(std::istream& in, point& p) {
    in >> p.first >> p.second;
    return in;
}

struct input {
    input(unsigned size, unsigned visit) : points_(size), visit_(visit) {}
    unsigned size() const { return points_.size(); }
    const point& operator[](unsigned idx) const { return points_[idx]; }
    point& operator[](unsigned idx) { return points_[idx]; }
    
    unsigned visit_;
    std::vector<point> points_;
};

void random_input(unsigned size, unsigned visit, unsigned max_coord) {
    std::ofstream in_file(in_path);
    in_file << size << ' ' << visit << '\n';
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> distr(0, max_coord - 1);
    for(int _ = 0; _ < size; _++) {
        int x = distr(gen), y = distr(gen);
        in_file << x << ' ' << y << '\n';
    }
}

input read_from_file() {
    std::ifstream in_file(in_path);
    unsigned size, visit;
    in_file >> size >> visit;
    input inp(size, visit);
    for(unsigned i = 0; i < size; i++) {
        in_file >> inp[i];
    }
    return inp;
}