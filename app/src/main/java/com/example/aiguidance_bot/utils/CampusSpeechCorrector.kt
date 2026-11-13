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

        // Labs & Makmal acoustic slips
        Regex("""(?i)\bprogram\s+(?:that|dat)\s*one\b""") to "Programming Lab 1",
        Regex("""(?i)\bprogram\s+(?:that|dat)\s*(?:to|too|two)\b""") to "Programming Lab 2",
        Regex("""(?i)\bai\s*lab\s*(?:tour|for|door|four)\b""") to "AI Lab 4",
        Regex("""(?i)\bai\s*lab\s*(?:tree|free|three)\b""") to "AI Lab 3",
        Regex("""(?i)\bai\s*lab\s*(?:to|too|two)\b""") to "AI Lab 2",
        Regex("""(?i)\bai\s*lab\s*(?:that|dat)\s*one\b""") to "AI Lab 1",
        Regex("""(?i)\bai\s*lab\s*(\d{1,2})\b""") to "Makmal AI $1",
        Regex("""(?i)\bmakmal\s*ai\s*(?:tour|for|door|four)\b""") to "Makmal AI 4",
        Regex("""(?i)\bmakmal\s*ai\s*(?:tree|free|three)\b""") to "Makmal AI 3",
        Regex("""(?i)\bmakmal\s*ai\s*(?:to|too|two)\b""") to "Makmal AI 2",
        Regex("""(?i)\bmakmal\s*ai\s*(?:that|dat)\s*one\b""") to "Makmal AI 1",

        // Other campus locations
        Regex("""(?i)\bsee\s*act\b""") to "C-ACT",
        Regex("""(?i)\bsea\s*act\b""") to "C-ACT",
        Regex("""(?i)\bc\s+act\b""") to "C-ACT",
        Regex("""(?i)\bsoft\s*eng\b""") to "Software Engineering Lab",
        Regex("""(?i)\bshort\s*part\b""") to "short path",
        Regex("""(?i)\bshot\s*path\b""") to "short path",
        Regex("""(?i)\btoliet\b""") to "toilet",
        Regex("""(?i)\blibary\b""") to "library"
    )

    /**
     * Corrects recognized speech transcript using campus phonetic rules.
     */
    fun correctTranscript(rawText: String): String {
        var text = rawText.trim()
        if (text.isEmpty()) return text

        for ((regex, replacement) in REPLACEMENTS) {
            text = regex.replace(text, replacement)
        }
        return text
    }
}
