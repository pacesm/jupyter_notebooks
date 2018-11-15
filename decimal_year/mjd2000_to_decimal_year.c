/*
 * decimal_year =  mjd2000_to_decimal_year(mjd2000)
 *
 * Matlab function converting decimal Modified Julian Dates truncated at
 * year 2000 (MJD2000) to decimal years.
 *
 * The conversion considers leap years and the whole decimal years are
 * aligned with ends of the calendar years.
 *
 * This is a MEX file for MATLAB.
 *
 *
 * @file mjd2000_to_decimal_year.c
 * @author Martin Paces <martin.paces@eox.at>
 * @brief Time Conversion Subroutines
 *
 * Time conversion subroutines.
 *
 * Copyright (C) 2018 EOX IT Services GmbH
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies of this Software or works derived from this Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
*/

#include "mex.h"
#include "time_conversion.h"


static void convert_mjd2000_to_to_decimal_year(
    double *out, const double *in, size_t size
) {
    for (size_t i = 0; i < size; ++i) {
        out[i] = mjd2k_to_decimal_year(in[i]);
    }
}


void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

    /* checking input/output counts */
    if (1 != nrhs) {
        mexErrMsgIdAndTxt(
            "mjd2000_to_decimal_year::nrhs", "One input required."
        );
    }

    if (1 != nlhs) {
        mexErrMsgIdAndTxt(
            "mjd2000_to_decimal_year::nlhs", "One output required."
        );
    }

    /* checking input type */
    if (!mxIsDouble(prhs[0]) || mxIsComplex(prhs[0])) {
        mexErrMsgIdAndTxt(
            "mjd2000_to_decimal_year::notDouble", "Input must be double."
        );
    }

    /* checking input dimension */
    const mwSize ndim = mxGetNumberOfDimensions(prhs[0]);
    const mwSize *dims = mxGetDimensions(prhs[0]);

    if (2 != ndim) {
        mexErrMsgIdAndTxt(
            "mjd2000_to_decimal_year::wrongDimension",
            "Regular 2D matrix expected."
        );
    }

    /* creating output */
    plhs[0] = mxCreateDoubleMatrix(dims[0], dims[1], mxREAL);

    /* element-by-element time conversion */

    convert_mjd2000_to_to_decimal_year(
        mxGetData(plhs[0]), mxGetData(prhs[0]), dims[0] * dims[1]
    );
}
