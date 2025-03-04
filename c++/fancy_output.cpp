#include<fstream>
#include<vector>

constexpr uint32_t little_endian(uint32_t num) {
    char byts[4] = {num >> 0, num >> 8, num >> 16, num >> 24};
    return *(uint32_t*)byts;
}

struct bmp_file_header {
    uint16_t file_type = 0x4D42; // BM in ascii
    uint32_t file_size;
    uint16_t reserved1 = 0;
    uint16_t reserved2 = 0;
    uint32_t offset_data = 0;
};

struct bmp_info_header {
    uint32_t size = sizeof(bmp_info_header);
    int32_t width;
    int32_t height;
    uint16_t planes = 1; // No. of planes for the target device, this is always 1
    uint16_t bit_count = 32;
    uint32_t compression = 0; // uncompressed
    uint32_t size_image = 0; // uncompressed image
    int32_t x_pixels_per_meter = 1;
    int32_t y_pixels_per_meter = 1;
    uint32_t colors_used = 0; // 0 is for max number of colors allowed by bit_count
    uint32_t colors_important = 0; // 0 is for all colors are required
};

struct bmp_color_header { // c++ contains 32bit ints with big-endian but little requires
    uint32_t red_mask = little_endian(0x00ff0000);
    uint32_t green_mask = little_endian(0x0000ff00);
    uint32_t blue_mask = little_endian(0x000000ff);
    uint32_t alpha_mask = little_endian(0xff000000);
    uint32_t color_space_type = little_endian(0x73524742); // sRGB in ascii
    uint32_t unused[16]{ 0 };                // Unused data for sRGB color space
};

using dot = std::pair<int, int>;

class bmp {
public:
    bmp(std::string path, unsigned width, unsigned height) : file_(path, std::ios::binary),
                                                             width_(width),
                                                             height_(height),
                                                             matrix_(width_*height_, little_endian(0xffffffff)) {
        bfh_.file_size = little_endian(14 + 40 + 84 + bih_.bit_count / 8 * width_ * height_);
        bih_.width = little_endian(width_);
        bih_.height = little_endian(height_);
    }

    void save() {
        file_.seekp(0);
        file_.write((const char*)&bfh_, 14);
        file_.write((const char*)&bih_, 40);
        file_.write((const char*)&bch_, 84);
        file_.write((const char*)matrix_.data(), bih_.bit_count / 8 * width_ * height_);
    }

    void draw_rect(dot left, dot right, uint32_t color) {
        color = little_endian(color);
        for(unsigned ln = left.second; ln < right.second; ln++)
            std::fill(matrix_.begin() + ln * width_ + left.first, matrix_.begin() + ln * width_ + right.first, color);
    }
    void draw_line(dot p1, dot p2, unsigned width, uint32_t color) {
        int A = p1.second - p2.second;
        int B = p2.first - p1.first;
        int C = -(A*p1.first + B*p1.second);
        dot now = p1;
        while(true) {
            dot left{now.first - width / 2, now.second - width / 2};
            dot right{now.first + (width - width / 2), now.second + (width - width / 2)};
            draw_rect(left, right, color);

            if(now == p2)
                return;

            if(abs(A) < abs(B)) {
                (now.first < p2.first) ? now.first++ : now.first--;
                now.second = -(A * now.first + C) / B;
            }
            else {
                (now.second < p2.second) ? now.second++ : now.second--;
                now.first = -(B * now.second + C) / A;
            }
        }
    }
private:
    std::ofstream file_;
    unsigned width_, height_;
    std::vector<uint32_t> matrix_;
    
    bmp_file_header bfh_;
    bmp_info_header bih_;
    bmp_color_header bch_;
};