#include "parser.h"


PYBIND11_MODULE(pyparser, m) {
    py::class_<Parser>(m, "Parser")
        .def(py::init<py::object>())
        .def("parse_next", &Parser::parse_next)
        .def("header", &Parser::header)
        .def("all_data", &Parser::all_data)
        .def("has_clocks", &Parser::has_clocks)
        .def("has_evals", &Parser::has_evals);
}