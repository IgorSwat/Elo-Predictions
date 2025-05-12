#pragma once

#include "buffer.h"
#include "states.h"
#include <unordered_map>


// -----------------
// Parser parameters
// -----------------

constexpr int BUFFER_SIZE = 65536;
constexpr int STORAGE_SIZE = 32768;


// ----------
// PGN parser
// ----------

// This is a lightweight PGN parsing class
// - Parses PGN headers and stores all PGN data
// - Cannot parse moves
class Parser
{
public:
    Parser(py::object reader) : m_buffer(reader), m_stream(&m_buffer) {}

    bool parse_next();

    // Getters
    std::string header(std::string h_name) { return m_headers[h_name]; }
    std::string all_data() { return std::string(m_data.begin(), m_data.begin() + m_data_size); }
    bool has_clocks() const { return m_clocks;}
    bool has_evals() const { return m_evals;}

private:
    // Data connection - buffer & stream
    StreamBuffer<BUFFER_SIZE> m_buffer;
    std::istream m_stream;                                      // We get data from this one

    // PGN data
    std::unordered_map<std::string, std::string> m_headers;     // PGN headers mapping (name - value)
    std::array<char, STORAGE_SIZE> m_data;                      // An entire PGN
    std::size_t m_data_size = 0;
    bool m_clocks = false;
    bool m_evals = false;

    // Parser state
    State m_curr_state = EXPECTING_ANYTHING;
    std::string m_tag_name = "";
    std::string m_tag_value = "";
};