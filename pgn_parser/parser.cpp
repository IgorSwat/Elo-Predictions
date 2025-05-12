#include "parser.h"
#include <cctype>


// ------------------
// PGN parser methods
// ------------------

bool Parser::parse_next()
{
    // Start with resetting the storage (by resetting it's size pointer) and state
    m_headers.clear();
    m_data_size = 0;
    m_curr_state = EXPECTING_ANYTHING;
    m_clocks = false;
    m_evals = false;

    while (true) {
        int bt = m_stream.get();

        if (bt == std::char_traits<char>::eof())
            return false;

        char c = static_cast<char>(bt);

        m_data[m_data_size++] = c;

        // React to the obtained character from PGN notation
        if (m_curr_state == EXPECTING_ANYTHING && c == '[') {
            m_curr_state = INSIDE_TAG_NAME;
            m_tag_name = "";
        }
        else if (m_curr_state == INSIDE_TAG_NAME && c != ' ')
            m_tag_name += c;
        else if (m_curr_state == INSIDE_TAG_NAME && c == ' ') {
            m_curr_state = INSIDE_TAG_VALUE;
            m_tag_value = "";
        }
        else if (m_curr_state == INSIDE_TAG_VALUE && c != '"' && c != ']')
            m_tag_value += c;
        else if (m_curr_state == INSIDE_TAG_VALUE && c == ']') {
            m_headers[m_tag_name] = m_tag_value;
            m_curr_state = EXPECTING_ANYTHING;
        }
        else if (m_curr_state == EXPECTING_ANYTHING && c == '{')
            m_curr_state = INSIDE_COMMENT;
        else if (m_curr_state == INSIDE_COMMENT && c == 'e')
            m_evals = true;
        else if (m_curr_state == INSIDE_COMMENT && c == 'c')
            m_clocks = true;
        else if (m_curr_state == INSIDE_COMMENT && c == '}')
            m_curr_state = EXPECTING_ANYTHING;
        else if (m_curr_state == EXPECTING_ANYTHING && c == '-' && m_data[m_data_size - 2] != 'O')
            m_curr_state = m_data[m_data_size - 2] == '2' ? EXPECTING_END_SCORE_DRAW : EXPECTING_END_SCORE_WIN;
        else if (m_curr_state == EXPECTING_END_SCORE_WIN)
            break;
        else if (m_curr_state == EXPECTING_END_SCORE_DRAW && c == '2')
            break;
        else if (m_curr_state == EXPECTING_ANYTHING && c == '*')        // Some weird correspondance game notation
            break;
    }

    return true;
}