#include "pch.h"
#include <iostream>
#include <vector>

#define DLLEXPORT extern "C" __declspec(dllexport)

/*
file was specifically built using no external dependencies!!
compiled using x64 architecture and only x64
main entry point for this file is the CallPricing function, which is called as a DLL from
my python program using CTYPEs in order to price options contracts very quickly.
The intention is to keep this c plus plus file as fast and lean as possible due to the
magnitude of calculations we have to perform. 500 iterations seems to strike an optimal
balance between pricing accuracy and speed.
*/

DLLEXPORT double CallPricing(float s, float k, float rf, float t, float v)
{
    int i, j;
    const int n = 500;

    // the divisor is 1 / 365, the division is already computed
    double h = (t / (n * 365));

    double up = std::exp(v * std::sqrt(2 * h));
    double down = std::exp(v * std::sqrt(2 * h));

    double rfr = exp(0.5 * rf * h);

    double denominator = (std::exp(v * std::sqrt(0.5 * h)) - exp(-v * std::sqrt(0.5 * h)));

    double pu = pow((rfr - std::exp(-v * std::sqrt(0.5 * h))) / denominator, 2);
    double pd = pow((std::exp(v * std::sqrt(0.5 * h)) - rfr) / denominator, 2);
    double pm = 1.0 - pu - pd;


    // processing terminal stock price
    std::vector<std::vector<double> > S(2 * n + 1, std::vector<double>(n + 1));

    for (j = 0; j <= n; j++)
        for (i = 0; i <= 2 * j; i++)
            S[i][j] = s * pow(up, double(j - i));


    std::vector<std::vector<double> > V(2 * n + 1, std::vector<double>(n + 1));
    // Compute terminal payoffs
    for (i = 0; i <= 2 * n; i++) {
        V[i][n] = max(S[i][n] - k, 0.0);
    }

    for (j = n - 1; j >= 0; j--) {
        for (i = 0; i <= 2 * j; i++) {
            V[i][j] = max(S[i][j] - k, exp(-rf * h) * (pu * V[i][j + 1] + pm * V[i + 1][j + 1] + pd * V[i + 2][j + 1]));
        }
    }
    return V[0][0];
}

DLLEXPORT double PutPricing(float s, float k, float rf, float t, float v)
{
    int i, j;
    const int n = 500;

    // the divisor is 1 / 365, the division is already computed
    double h = (t / (n * 365));

    double up = std::exp(v * std::sqrt(2 * h));
    double down = std::exp(v * std::sqrt(2 * h));

    double rfr = exp(0.5 * rf * h);

    double denominator = (std::exp(v * std::sqrt(0.5 * h)) - exp(-v * std::sqrt(0.5 * h)));

    double pu = pow((rfr - std::exp(-v * std::sqrt(0.5 * h))) / denominator, 2);
    double pd = pow((std::exp(v * std::sqrt(0.5 * h)) - rfr) / denominator, 2);
    double pm = 1.0 - pu - pd;

    // processing terminal stock price
    std::vector<std::vector<double>> S(2 * n + 1, std::vector<double>(n + 1));
    for (j = 0; j <= n; j++)
        for (i = 0; i <= 2 * j; i++)
            S[i][j] = s * pow(up, double(j - i));

    std::vector<std::vector<double>> V(2 * n + 1, std::vector<double>(n + 1));
    // Compute terminal payoffs
    for (i = 0; i <= 2 * n; i++) {
        V[i][n] = max(k - S[i][n], 0.0);
    }

    for (j = n - 1; j >= 0; j--) {
        for (i = 0; i <= 2 * j; i++) {
            V[i][j] = max(k - S[i][j], exp(-rf * h) * (pu * V[i][j + 1] + pm * V[i + 1][j + 1] + pd * V[i + 2][j + 1]));
        }
    }
    return V[0][0];
}

int main(int argc, char** argv)
{
    return 0;
}
