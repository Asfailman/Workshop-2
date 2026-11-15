package com.example.aiguidance_bot.utils

import java.util.regex.Pattern

/**
 * CampusSpeechCorrector
 *
 * Client-side phonetic NLP correction engine for campus queries.
 * Fixes common acoustic slips and speech recognition misunderstandings
 * before sending to the assistant, ensuring high accuracy on local UTeM terms.
 */
object CampusSpeechCorrector {

    private val REPLACEMENTS: List<Pair<Regex, String>> = listOf(
        // Class vs Glass acoustic slips (minimal pair: /klæs/ vs /glæs/)
        Regex("""(?i)\bsurrounding\s+glass(?:es)?\b""") to "surrounding class",
        Regex("""(?i)\bglass\s*rooms?\b""") to "classroom",
        Regex("""(?i)\b(?:in|at|near|beside|into)\s+glass(?:es)?\b""") to "in class",
        Regex("""(?i)\bglass\b""") to "class",
        Regex("""(?i)\bglasses\b""") to "classes",

        // Bilik Kuliah / BK acoustic slips
        Regex("""(?i)\bbilly\s*kulia\s*(?:to|too|two)\b""") to "Bilik Kuliah 2",
        Regex("""(?i)\bbilly\s*kulia\s*(?:tree|free|three)\b""") to "Bilik Kuliah 3",
        Regex("""(?i)\bbilly\s*kulia\s*(?:tour|for|door|four)\b""") to "Bilik Kuliah 4",
        Regex("""(?i)\bbilly\s*kulia\s*(?:that|dat)\s*one\b""") to "Bilik Kuliah 1",
        Regex("""(?i)\bbilly\s*kulia\s*(\d{1,2})\b""") to "Bilik Kuliah $1",
        Regex("""(?i)\bbilly\s*kulia\b""") to "Bilik Kuliah",
        Regex("""(?i)\bbillie\s*kulia\b""") to "Bilik Kuliah",
        Regex("""(?i)\bbilly\s*clear\b""") to "Bilik Kuliah",
        Regex("""(?i)\bbk\s*(?:to|too|two)\b""") to "BK 2",
        Regex("""(?i)\bbk\s*(?:tree|free|three)\b""") to "BK 3",
        Regex("""(?i)\bbk\s*(?:tour|for|door|four)\b""") to "BK 4",
        Regex("""(?i)\bbk\s*(?:that|dat)\s*one\b""") to "BK 1",

        // Dewan Kuliah / DK acoustic slips
        Regex("""(?i)\b(?:where\s+did\s+europe|where\s+do\s+you\s+and\s+europe)\b""") to "where is Dewan Kuliah",
        Regex("""(?i)\b(?:the\s+one\s+cool\s+yeah|the\s+one\s+kulia)\b""") to "Dewan Kuliah",
        Regex("""(?i)\b(?:die\s*k|day\s*k|de\s*k)\b""") to "DK",
        Regex("""(?i)\bdk\s*(?:to|too|two)\b""") to "DK 2",
        Regex("""(?i)\bdk\s*(?:tree|free|three)\b""") to "DK 3",
        Regex("""(?i)\bdk\s*(?:tour|for|door|four)\b""") to "DK 4",

        // Labs acoustic slips & normalization (always keep as English: AI Lab, Programming Lab, etc.)
        Regex("""(?i)\bprogram\s+(?:that|dat)\s*one\b""") to "Programming Lab 1",
        Regex("""(?i)\bprogram\s+(?:that|dat)\s*(?:to|too|two)\b""") to "Programming Lab 2",
        Regex("""(?i)\bprog(?:ram(?:ming)?)?\s*lab\s*(\d{1,2})\b""") to "Programming Lab $1",
        Regex("""(?i)\bprog(?:ram(?:ming)?)?\s*lab\b(?!\s*[0-9])""") to "Programming Lab 1",
        Regex("""(?i)\bmakmal\s*program(?:ming|aturcaraan)?\s*(\d{1,2})\b""") to "Programming Lab $1",
        Regex("""(?i)\bmakmal\s*program(?:ming|aturcaraan)?\b""") to "Programming Lab 1",

        Regex("""(?i)\bai\s*lab\s*(?:tour|for|door|four)\b""") to "AI Lab 4",
        Regex("""(?i)\bai\s*lab\s*(?:tree|free|three)\b""") to "AI Lab 3",
        Regex("""(?i)\bai\s*lab\s*(?:to|too|two)\b""") to "AI Lab 2",
        Regex("""(?i)\bai\s*lab\s*(?:that|dat)\s*one\b""") to "AI Lab 1",
        Regex("""(?i)\bai\s*lab\s*(\d{1,2})\b""") to "AI Lab $1",
        Regex("""(?i)\bai\s*lab\b(?!\s*[0-9])""") to "AI Lab 1",
        Regex("""(?i)\bmakmal\s*ai\s*(?:tour|for|door|four)\b""") to "AI Lab 4",
        Regex("""(?i)\bmakmal\s*ai\s*(?:tree|free|three)\b""") to "AI Lab 3",
        Regex("""(?i)\bmakmal\s*ai\s*(?:to|too|two)\b""") to "AI Lab 2",
        Regex("""(?i)\bmakmal\s*ai\s*(?:that|dat)\s*one\b""") to "AI Lab 1",
        Regex("""(?i)\bmakmal\s*ai\s*(\d{1,2})\b""") to "AI Lab $1",
        Regex("""(?i)\bmakmal\s*ai\b""") to "AI Lab 1",

        Regex("""(?i)\bmakmal\s*kejuruteraan\s*perisian\s*(\d{1,2})\b""") to "Software Engineering Lab $1",
        Regex("""(?i)\bmakmal\s*kejuruteraan\s*perisian\b""") to "Software Engineering Lab 1",
        Regex("""(?i)\bsoft(?:ware)?\s*eng(?:ineering)?\s*lab\s*(\d{1,2})\b""") to "Software Engineering Lab $1",
        Regex("""(?i)\bsoft(?:ware)?\s*eng(?:ineering)?\s*lab\b""") to "Software Engineering Lab 1",

        Regex("""(?i)\bmakmal\s*rangkaian\s*(\d{1,2})\b""") to "Network Lab $1",
        Regex("""(?i)\bmakmal\s*rangkaian\b""") to "Network Lab 1",
        Regex("""(?i)\bnet(?:work)?\s*lab\s*(\d{1,2})\b""") to "Network Lab $1",
        Regex("""(?i)\bnet(?:work)?\s*lab\b""") to "Network Lab 1",

        Regex("""(?i)\bmakmal\s*pangkalan\s*data\s*(\d{1,2})\b""") to "Database Lab $1",
        Regex("""(?i)\bmakmal\s*pangkalan\s*data\b""") to "Database Lab 1",
        Regex("""(?i)\bdata(?:base)?\s*lab\s*(\d{1,2})\b""") to "Database Lab $1",
        Regex("""(?i)\bdata(?:base)?\s*lab\b""") to "Database Lab 1",

        Regex("""(?i)\bmakmal\s*multimedia\s*(\d{1,2})\b""") to "Multimedia Lab $1",
        Regex("""(?i)\bmakmal\s*multimedia\b""") to "Multimedia Lab 1",
        Regex("""(?i)\bmulti(?:media)?\s*lab\s*(\d{1,2})\b""") to "Multimedia Lab $1",
        Regex("""(?i)\bmulti(?:media)?\s*lab\b""") to "Multimedia Lab 1",

        // Other campus locations
        Regex("""(?i)\bsee\s*act\b""") to "C-ACT",
        Regex("""(?i)\bsea\s*act\b""") to "C-ACT",
        Regex("""(?i)\bc\s+act\b""") to "C-ACT",
        Regex("""(?i)\bsoft\s*eng\b""") to "Software Engineering Lab",
        Regex("""(?i)\blap\b""") to "lab",
        Regex("""(?i)\blaps\b""") to "labs",
        Regex("""(?i)\bshort\s*part\b""") to "short path",
        Regex("""(?i)\bshot\s*path\b""") to "short path",
        Regex("""(?i)\btoliet\b""") to "toilet",
        Regex("""(?i)\blibary\b""") to "library"
    )

    private val NUMBER_WORDS: List<Pair<Regex, String>> = listOf(
        Regex("""(?i)\b(?:zero|sifar|kosong)\b""") to "0",
        Regex("""(?i)\b(?:one|satu|first|pertama)\b""") to "1",
        Regex("""(?i)\b(?:two|dua|second|kedua)\b""") to "2",
        Regex("""(?i)\b(?:three|tiga|third|ketiga)\b""") to "3",
        Regex("""(?i)\b(?:four|empat|fourth|keempat)\b""") to "4",
        Regex("""(?i)\b(?:five|lima|fifth|kelima)\b""") to "5",
        Regex("""(?i)\b(?:six|enam|sixth|keenam)\b""") to "6",
        Regex("""(?i)\b(?:seven|tujuh|seventh|ketujuh)\b""") to "7",
        Regex("""(?i)\b(?:eight|lapan|eighth|kelapan)\b""") to "8",
        Regex("""(?i)\b(?:nine|sembilan|ninth|kesembilan)\b""") to "9",
        Regex("""(?i)\b(?:ten|sepuluh|tenth|kesepuluh)\b""") to "10",
        Regex("""(?i)\b(?:eleven|sebelas)\b""") to "11",
        Regex("""(?i)\b(?:twelve|dua\s*belas)\b""") to "12",
        Regex("""(?i)\b(?:thirteen|tiga\s*belas)\b""") to "13",
        Regex("""(?i)\b(?:fourteen|empat\s*belas)\b""") to "14",
        Regex("""(?i)\b(?:fifteen|lima\s*belas)\b""") to "15",
        Regex("""(?i)\b(?:sixteen|enam\s*belas)\b""") to "16"
    )

    private val FILLER_REGEX = Regex("""(?i)\b(?:u+h+m*|h+m+|e+r+m*|a+h+|e+h+|e+m+|a+a+)\b""")

    /**
     * Corrects recognized speech transcript using campus phonetic rules.
     */
    fun correctTranscript(rawText: String): String {
        var text = rawText.trim()
        if (text.isEmpty()) return text

        // 1. Strip vocal fillers (uh, um, hmm, er, etc.)
        text = FILLER_REGEX.replace(text, "")
        text = text.replace(Regex("""\s+"""), " ").trim()

        // 2. Convert spoken number words to digits (English & Malay)
        for ((regex, replacement) in NUMBER_WORDS) {
            text = regex.replace(text, replacement)
        }

        // 3. Apply campus phonetic & room corrections
        for ((regex, replacement) in REPLACEMENTS) {
            text = regex.replace(text, replacement)
        }

        return text.replace(Regex("""\s+"""), " ").trim()
    }
}
