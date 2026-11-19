package com.example.aiguidance_bot.data

import android.content.Context
import android.content.SharedPreferences

object PreferencesHelper {

    private const val PREF_NAME = "aiguidance_settings_prefs"
    private const val KEY_THEME_MODE = "theme_mode" // "BRIGHT" or "DARK"
    private const val KEY_FONT_SIZE_SP = "font_size_sp" // 14f, 16f, or 20f

    const val THEME_BRIGHT = "BRIGHT"
    const val THEME_DARK = "DARK"

    const val FONT_SIZE_SMALL = 14f
    const val FONT_SIZE_MEDIUM = 16f
    const val FONT_SIZE_LARGE = 20f

    private fun getPrefs(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }

    fun getThemeMode(context: Context): String {
        return getPrefs(context).getString(KEY_THEME_MODE, THEME_BRIGHT) ?: THEME_BRIGHT
    }

    fun setThemeMode(context: Context, themeMode: String) {
        getPrefs(context).edit().putString(KEY_THEME_MODE, themeMode).apply()
    }

    fun getFontSizeSp(context: Context): Float {
        return getPrefs(context).getFloat(KEY_FONT_SIZE_SP, FONT_SIZE_MEDIUM)
    }

    fun setFontSizeSp(context: Context, fontSizeSp: Float) {
        getPrefs(context).edit().putFloat(KEY_FONT_SIZE_SP, fontSizeSp).apply()
    }

    fun resetToDefaults(context: Context) {
        setThemeMode(context, THEME_BRIGHT)
        setFontSizeSp(context, FONT_SIZE_MEDIUM)
    }
}
