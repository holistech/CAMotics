/******************************************************************************\

             CAMotics is an Open-Source simulation and CAM software.
     Copyright (C) 2011-2021 Joseph Coffland <joseph@cauldrondevelopment.com>

       This program is free software: you can redistribute it and/or modify
       it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 2 of the License, or
                       (at your option) any later version.

         This program is distributed in the hope that it will be useful,
          but WITHOUT ANY WARRANTY; without even the implied warranty of
          MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
                   GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
      along with this program.  If not, see <http://www.gnu.org/licenses/>.

\******************************************************************************/

#pragma once


// Only set the error if Python doesn't already have one pending: a C++
// exception originating from a failed Python call already carries the more
// precise original exception, which we must not overwrite.
#define CATCH_PYTHON                                            \
  catch (const cb::Exception &e) {                              \
    if (!PyErr_Occurred())                                      \
      PyErr_SetString(PyExc_RuntimeError, SSTR(e).c_str());     \
  } catch (const std::exception &e) {                           \
    if (!PyErr_Occurred())                                      \
      PyErr_SetString(PyExc_RuntimeError, e.what());            \
  } catch (...) {                                               \
    if (!PyErr_Occurred())                                      \
      PyErr_SetString(PyExc_RuntimeError, "Unknown exception"); \
  }
