/*
 * mjd2000 =  decimal_year_to_mjd2000(decimal_year)
 *
 * Matlab function converting decimal years to Modified Julian Dates
 * truncated at year 2000 (MJD2000).
 *
 * The conversion considers leap years and the whole decimal years are
 * aligned with ends of the calendar years.
 *
 * This is a MEX file for MATLAB.
 *
 *
 * @file decimal_year_to_mjd2000.c
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


static void convert_decimal_year_to_to_mjd2000(
    double *out, const double *in, size_t size
) {
    for (size_t i = 0; i < size; ++i) {
        out[i] = decimal_year_to_mjd2k(in[i]);
    }
}


void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

    /* checking input/output counts */
    if (1 != nrhs) {
        mexErrMsgIdAndTxt(
            "decimal_year_to_mjd2000::nrhs", "One input required."
        );
    }

    if (1 != nlhs) {
        mexErrMsgIdAndTxt(
            "decimal_year_to_mjd2000::nlhs", "One output required."
        );
    }

    /* checking input type */
    if (!mxIsDouble(prhs[0]) || mxIsComplex(prhs[0])) {
        mexErrMsgIdAndTxt(
            "decimal_year_to_mjd2000::notDouble", "Input must be double."
        );
    }

    /* checking input dimension */
    const mwSize ndim = mxGetNumberOfDimensions(prhs[0]);
    const mwSize *dims = mxGetDimensions(prhs[0]);

    if (2 != ndim) {
        mexErrMsgIdAndTxt(
            "decimal_year_to_mjd2000::wrongDimension",
            "Regular 2D matrix expected."
        );
    }

    /* creating output */
    plhs[0] = mxCreateDoubleMatrix(dims[0], dims[1], mxREAL);

    /* element-by-element time conversion */

    convert_decimal_year_to_to_mjd2000(
        mxGetData(plhs[0]), mxGetData(prhs[0]), dims[0] * dims[1]
    );
}
