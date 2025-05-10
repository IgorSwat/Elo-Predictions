#pragma once

#include <array>
#include <exception>
#include <iostream>
#include <string>
#include <streambuf>
#include <type_traits>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>


namespace py = pybind11;


// -------------------
// Stream buffer class
// -------------------

// An efficient implementation of simple buffering for std::istream
template <int SIZE = 4096>
class StreamBuffer : public std::streambuf
{
public:
    StreamBuffer(py::object reader) : m_reader(reader) {
        char* base = m_buffer.data();
        setg(base, base, base);
    }

protected:
    // This method is called when the get area is exhausted
    int_type underflow() override {
        if (gptr() < egptr()) 
            return traits_type::to_int_type(*gptr());

        // Call reader.read(buffer_size)
        py::object data = m_reader.attr("read")(m_buffer.size());
        if (data.is_none()) return traits_type::eof();

        // Expect bytes or str
        std::string s;
        if (py::isinstance<py::bytes>(data)) {
            s = data.cast<std::string>();
        } else if (py::isinstance<py::str>(data)) {
            s = data.cast<std::string>();
        } else {
            throw std::runtime_error("reader.read() must return str or bytes");
        }

        if (s.empty()) return traits_type::eof();

        if (s.size() > m_buffer.size()) {
            throw std::runtime_error("reader returned too much data for buffer");
        }

        std::memcpy(m_buffer.data(), s.data(), s.size());

        char* base = m_buffer.data();
        setg(base, base, base + s.size());

        return traits_type::to_int_type(*gptr());
    }

private:
    // Python reader adaptation
    py::object m_reader;

    // Buffer container
    std::array<char, SIZE> m_buffer;
};