#include<random>

#include"input_stuff.cpp"

constexpr double dist(point p1, point p2) {
    return hypot(p1.first - p2.first, p1.second - p2.second);
}

using path = std::vector<point>;

double length(const path& pth) {
    double res = 0;
    for(auto it = pth.begin(); it + 1 != pth.end(); it++) {
        res += dist(*it, *(it + 1));
    }
    return res;
}

const double base_temp = 1.0;

class Otjig {
public:
    Otjig() : rd(), gen(rd()) {}

    void optimise(path* pth, unsigned iters = 1000) {
        pth_ = pth;
        temp_ = base_temp;
        cur_len_ = length(*pth_);
        for(unsigned _ = 0; _ < iters; _++)
            iterate();
    }
private:
    double el_dist(unsigned id1, unsigned id2) const {
        return dist(pth_->at(id1), pth_->at(id2));
    }
    double escape_chance(double new_len) const {
        return std::exp((cur_len_ - new_len) / temp_);
    }
    void cool() {
        temp_ *= 0.99;
    }
    // main optimisation function
    void iterate() {
        // choosing swapping elements
        std::uniform_int_distribution<> id_distr(1, pth_->size() - 1);
        unsigned swap1 = id_distr(gen);
        unsigned swap2 = id_distr(gen);

        // correcting choose
        if(swap1 == swap2)
            swap2 = (swap1 == pth_->size() - 1) ? 1 : swap1 + 1;
        if(swap1 > swap2)
            std::swap(swap1, swap2);
        
        // calculating length after swap
        double new_len = cur_len_;
        new_len += el_dist(swap1 - 1, swap2) - el_dist(swap1 - 1, swap1);
        new_len += el_dist(swap1 + 1, swap2) - el_dist(swap1 + 1, swap1);

        new_len += el_dist(swap2 - 1, swap1) - el_dist(swap2 - 1, swap2);
        if(swap2 != pth_->size() - 1)
            new_len += el_dist(swap2 + 1, swap1) - el_dist(swap2 + 1, swap2);
        
        // decide to apply swap or not
        std::uniform_real_distribution<> std_distr(0.0, 1.0);
        double rnd_val = std_distr(gen);
        if(rnd_val < escape_chance(new_len)) { // if new len is less, chance > 1.0, which means its definetly true
            std::swap(pth_->at(swap1), pth_->at(swap2));
            cur_len_ = new_len;
        }
        cool();
    }
    std::random_device rd;
    std::mt19937 gen;

    path* pth_;
    double temp_;
    double cur_len_;
};