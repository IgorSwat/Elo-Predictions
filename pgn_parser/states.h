#pragma once


// -------------
// Parser states
// -------------

enum State {
    EXPECTING_ANYTHING = 0,     // A non-terminal state where we expect either a tag or move number

    INSIDE_TAG,                 // At any point inside a tag
    INSIDE_TAG_NAME,            // Expecting next bytes of tag name, ends with ' '
    INSIDE_TAG_VALUE,           // Expecting next bytes of tag value, ends with " or ]

    INSIDE_COMMENT,             // Indicated by { bracket, end with }

    EXPECTING_END_SCORE_DRAW,
    EXPECTING_END_SCORE_WIN,
    END                         // Terminal state
};