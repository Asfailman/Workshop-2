package com.example.aiguidance_bot.data

data class FtmkRoom(
    val id: String,
    val nameMalay: String,
    val nameEnglish: String,
    val block: String,
    val level: Int, // 1, 2, 3, or 4
    val category: String,
    val mapBiasX: Float = 0.5f,
    val mapBiasY: Float = 0.5f
)

object FtmkLocationDatabase {

    val rooms = listOf(
        // LEVEL 1 (ARAS 1)
        FtmkRoom("c_act", "C-ACT", "C-ACT", "Blok A", 1, "Administrative", 0.45f, 0.20f),
        FtmkRoom("lobi", "Lobi", "Lobby", "Blok A", 1, "Administrative", 0.55f, 0.20f),
        FtmkRoom("vr_studio_1", "Studio Realiti Maya", "Virtual Reality Studio", "Blok C1", 1, "Studio", 0.28f, 0.42f),
        FtmkRoom("bk14", "Bilik Kuliah 14", "Lecture Room 14", "Blok C1", 1, "Lecture Room", 0.24f, 0.48f),
        FtmkRoom("students_common", "Bilik Umum Pelajar", "Students' Common Room", "Blok C1", 1, "Common Area", 0.20f, 0.55f),
        FtmkRoom("bk12", "Bilik Kuliah 12", "Lecture Room 12", "Blok C1", 1, "Lecture Room", 0.16f, 0.62f),
        FtmkRoom("bk11", "Bilik Kuliah 11", "Lecture Room 11", "Blok C1", 1, "Lecture Room", 0.13f, 0.68f),
        FtmkRoom("bk9_10", "Bilik Kuliah 9 & 10", "Lecture Room 9 & 10", "Blok C1", 1, "Lecture Room", 0.10f, 0.74f),
        FtmkRoom("esport_lab", "Makmal e-Sport", "e-Sport Lab", "Blok C2", 1, "Lab", 0.35f, 0.58f),
        FtmkRoom("bk13", "Bilik Kuliah 13", "Lecture Room 13", "Blok C2", 1, "Lecture Room", 0.30f, 0.66f),
        FtmkRoom("mtds_lab", "Makmal MTDS", "MTDS Lab", "Blok C2", 1, "Lab", 0.26f, 0.74f),
        FtmkRoom("se_lab_1", "Makmal Kejuruteraan Perisian 1", "Software Engineering Lab 1", "Blok E1", 1, "Lab", 0.68f, 0.45f),
        FtmkRoom("se_lab_2", "Makmal Kejuruteraan Perisian 2", "Software Engineering Lab 2", "Blok E1", 1, "Lab", 0.72f, 0.51f),
        FtmkRoom("se_lab_3", "Makmal Kejuruteraan Perisian 3", "Software Engineering Lab 3", "Blok E1", 1, "Lab", 0.76f, 0.57f),
        FtmkRoom("bk5", "Bilik Kuliah 5", "Lecture Room 5", "Blok E1", 1, "Lecture Room", 0.80f, 0.63f),
        FtmkRoom("bk4", "Bilik Kuliah 4", "Lecture Room 4", "Blok E1", 1, "Lecture Room", 0.83f, 0.69f),
        FtmkRoom("bk3", "Bilik Kuliah 3", "Lecture Room 3", "Blok E1", 1, "Lecture Room", 0.86f, 0.75f),
        FtmkRoom("bk2", "Bilik Kuliah 2", "Lecture Room 2", "Blok E1", 1, "Lecture Room", 0.89f, 0.80f),
        FtmkRoom("bk1", "Bilik Kuliah 1", "Lecture Room 1", "Blok E1", 1, "Lecture Room", 0.92f, 0.85f),
        FtmkRoom("bk6", "Bilik Kuliah 6", "Lecture Room 6", "Blok E2", 1, "Lecture Room", 0.62f, 0.58f),
        FtmkRoom("bk7", "Bilik Kuliah 7", "Lecture Room 7", "Blok E2", 1, "Lecture Room", 0.65f, 0.63f),
        FtmkRoom("bk8", "Bilik Kuliah 8", "Lecture Room 8", "Blok E2", 1, "Lecture Room", 0.68f, 0.68f),
        FtmkRoom("prog_lab_1", "Makmal Pengaturcaraan 1", "Programming Lab 1", "Blok E2", 1, "Lab", 0.71f, 0.73f),
        FtmkRoom("prog_lab_2", "Makmal Pengaturcaraan 2", "Programming Lab 2", "Blok E2", 1, "Lab", 0.74f, 0.78f),
        FtmkRoom("biocore_lab", "Makmal Penyelidikan BIOCORE", "BIOCORE Research Lab", "Blok E2", 1, "Research Lab", 0.77f, 0.83f),
        FtmkRoom("optimass_lab", "Makmal Penyelidikan OPTIMASS", "OPTIMASS Research Lab", "Blok E2", 1, "Research Lab", 0.80f, 0.88f),

        // LEVEL 2 (ARAS 2)
        FtmkRoom("discussion_room", "Bilik Bincang", "Discussion Room", "Blok A", 2, "Meeting", 0.50f, 0.20f),
        FtmkRoom("clear_room", "Bilik CLeaR FTMK", "FTMK CLeaR Room", "Blok C1", 2, "Special Room", 0.28f, 0.42f),
        FtmkRoom("game_lab", "Makmal Permainan Komputer", "Computer Games Lab", "Blok C1", 2, "Lab", 0.24f, 0.48f),
        FtmkRoom("multimedia_lab_2", "Makmal Multimedia 2", "Multimedia Lab 2", "Blok C1", 2, "Lab", 0.20f, 0.55f),
        FtmkRoom("multimedia_lab_1", "Makmal Multimedia 1", "Multimedia Lab 1", "Blok C1", 2, "Lab", 0.16f, 0.62f),
        FtmkRoom("cybersecurity_center", "Cybersecurity Competence Center", "Cybersecurity Center", "Blok C2", 2, "Center", 0.35f, 0.58f),
        FtmkRoom("ccna_ccnp_lab", "Makmal CCNA & CCNP", "CCNA & CCNP Lab", "Blok C2", 2, "Lab", 0.30f, 0.66f),
        FtmkRoom("fiber_optic_lab", "Makmal Fiber Optic", "Fiber Optic Lab", "Blok C2", 2, "Lab", 0.26f, 0.74f),
        FtmkRoom("db_lab_3", "Makmal Pangkalan Data 3", "Database Lab 3", "Blok E1", 2, "Lab", 0.68f, 0.45f),
        FtmkRoom("db_lab_2", "Makmal Pangkalan Data 2", "Database Lab 2", "Blok E1", 2, "Lab", 0.72f, 0.51f),
        FtmkRoom("db_lab_1", "Makmal Pangkalan Data 1", "Database Lab 1", "Blok E1", 2, "Lab", 0.76f, 0.57f),
        FtmkRoom("net_lab_2", "Makmal Rangkaian 2", "Network Lab 2", "Blok E1", 2, "Lab", 0.80f, 0.63f),
        FtmkRoom("pet_lab", "Makmal Penyelidikan PET", "PET Research Lab", "Blok E1", 2, "Research Lab", 0.83f, 0.69f),
        FtmkRoom("ai_lab_3", "Makmal Kepintaran Buatan 3", "Artificial Intelligence Lab 3", "Blok E2", 2, "Lab", 0.62f, 0.58f),
        FtmkRoom("ai_lab_1", "Makmal Kepintaran Buatan 1", "Artificial Intelligence Lab 1", "Blok E2", 2, "Lab", 0.65f, 0.63f),
        FtmkRoom("ai_lab_2", "Makmal Kepintaran Buatan 2", "Artificial Intelligence Lab 2", "Blok E2", 2, "Lab", 0.68f, 0.68f),
        FtmkRoom("recap_room", "Bilik ReCap", "ReCap Room", "Blok E2", 2, "Special Room", 0.71f, 0.73f),
        FtmkRoom("ai_lab_4", "Makmal Kepintaran Buatan 4", "Artificial Intelligence Lab 4", "Blok E2", 2, "Lab", 0.74f, 0.78f),

        // LEVEL 3 (ARAS 3)
        FtmkRoom("admin_discussion", "Bilik Bincang Pentadbiran", "Administrative Discussion Room", "Blok A", 3, "Administrative", 0.50f, 0.20f),
        FtmkRoom("multimedia_lab_4", "Makmal Multimedia 4", "Multimedia Lab 4", "Blok C1", 3, "Lab", 0.28f, 0.42f),
        FtmkRoom("vr_lab", "Makmal Realiti Maya", "Virtual Reality Lab", "Blok C1", 3, "Lab", 0.24f, 0.48f),
        FtmkRoom("multimedia_lab_3", "Makmal Multimedia 3", "Multimedia Lab 3", "Blok C1", 3, "Lab", 0.20f, 0.55f),
        FtmkRoom("mini_theatre", "Studio Multimedia (Teater Mini)", "Multimedia Studio (Mini Theatre)", "Blok C1", 3, "Studio", 0.16f, 0.62f),
        FtmkRoom("audio_room_1", "Bilik Rakaman Audio 1", "Audio Recording Room 1", "Blok C1", 3, "Studio", 0.14f, 0.66f),
        FtmkRoom("audio_room_2", "Bilik Rakaman Audio 2", "Audio Recording Room 2", "Blok C1", 3, "Studio", 0.12f, 0.70f),
        FtmkRoom("shooting_studio", "Studio Pengambaran", "Shooting Studio", "Blok C1", 3, "Studio", 0.10f, 0.74f),
        FtmkRoom("huawei_lab", "Makmal Huawei", "Huawei Lab", "Blok C2", 3, "Lab", 0.35f, 0.58f),
        FtmkRoom("security_lab_2", "Makmal Keselamatan 2", "Security Lab 2", "Blok C2", 3, "Lab", 0.30f, 0.66f),
        FtmkRoom("wireless_lab", "Makmal Tanpa Wayar", "Wireless Lab", "Blok C2", 3, "Lab", 0.26f, 0.74f),
        FtmkRoom("systems_hardware_lab", "Makmal Sistem dan Perkakasan", "Systems and Hardware Lab", "Blok E1", 3, "Lab", 0.68f, 0.45f),
        FtmkRoom("systems_lab", "Makmal Sistem", "Systems Lab", "Blok E1", 3, "Lab", 0.72f, 0.51f),
        FtmkRoom("net_lab_1", "Makmal Rangkaian 1", "Network Lab 1", "Blok E1", 3, "Lab", 0.76f, 0.57f),
        FtmkRoom("exec_lab", "Makmal Eksekutif", "Executive Lab", "Blok E1", 3, "Lab", 0.80f, 0.63f),
        FtmkRoom("students_workshop", "Bengkel Pelajar", "Students' Workshop", "Blok E1", 3, "Workshop", 0.83f, 0.69f),
        FtmkRoom("skk_workshop", "Bengkel SKK", "SKK Workshop", "Blok E2", 3, "Workshop", 0.62f, 0.58f),
        FtmkRoom("robotics_lab", "Makmal Robotik", "Robotics Lab", "Blok E2", 3, "Lab", 0.65f, 0.63f),
        FtmkRoom("biti_workshop", "Bengkel BITI", "BITI Workshop", "Blok E2", 3, "Workshop", 0.68f, 0.68f),
        FtmkRoom("cmerp_lab", "Makmal CMERP", "CMERP Lab", "Blok E2", 3, "Lab", 0.71f, 0.73f),
        FtmkRoom("ideal_lab", "Makmal Penyelidikan IDEAL", "IDEAL Research Lab", "Blok E2", 3, "Research Lab", 0.74f, 0.78f),
        FtmkRoom("is3_lab", "Makmal Penyelidikan IS3", "IS3 Research Lab", "Blok E2", 3, "Research Lab", 0.77f, 0.83f),

        // LEVEL 4 (ARAS 4)
        FtmkRoom("seminar_hall", "Dewan Seminar", "Seminar Hall", "Blok A", 4, "Hall", 0.45f, 0.20f),
        FtmkRoom("main_meeting_room", "Bilik Mesyuarat Utama", "Main Meeting Room", "Blok A", 4, "Meeting", 0.55f, 0.20f),
        FtmkRoom("prog_lab_3", "Makmal Pengaturcaraan 3", "Programming Lab 3", "Blok E1", 4, "Lab", 0.68f, 0.48f),
        FtmkRoom("prog_lab_4", "Makmal Pengaturcaraan 4", "Programming Lab 4", "Blok E1", 4, "Lab", 0.74f, 0.58f),
        FtmkRoom("bitd_workshop", "Bengkel BITD", "BITD Workshop", "Blok E1", 4, "Workshop", 0.80f, 0.68f),
        FtmkRoom("advit_lab", "Makmal Penyelidikan AdViT", "AdViT Research Lab", "Blok E2", 4, "Research Lab", 0.65f, 0.60f),
        FtmkRoom("inforsnet_lab", "Makmal Penyelidikan INFORSNET", "INFORSNET Research Lab", "Blok E2", 4, "Research Lab", 0.72f, 0.72f)
    )

    fun findRoomByQuery(query: String): FtmkRoom? {
        val cleanQuery = query.lowercase().replace("\\s+".toRegex(), "")

        // 1. Lecture Room / Bilik Kuliah Shortcuts: BM (BK1..BK14) & EN (LR1..LR14)
        val bkMatch = reMatch("(?:bk|lr)(\\d+)", cleanQuery)
        if (bkMatch != null) {
            val room = rooms.find { it.id == "bk$bkMatch" || it.id == "bk${bkMatch}_10" }
            if (room != null) return room
        }

        // 2. Artificial Intelligence / Kepintaran Buatan: BM (MKB1..MKB4) & EN (AI1..AI4)
        val aiMatch = reMatch("(?:ai|mkb)(\\d+)", cleanQuery)
        if (aiMatch != null) {
            val room = rooms.find { it.id == "ai_lab_$aiMatch" }
            if (room != null) return room
        }

        // 3. Programming Lab / Makmal Pengaturcaraan: BM (MP1..MP4) & EN (PROG1..PROG4, PL1..PL4)
        val progMatch = reMatch("(?:prog|mp|pl)(\\d+)", cleanQuery)
        if (progMatch != null) {
            val room = rooms.find { it.id == "prog_lab_$progMatch" }
            if (room != null) return room
        }

        // 4. Software Engineering / Kejuruteraan Perisian: BM (MKP1..MKP3) & EN (SE1..SE3, SEL1..SEL3)
        val seMatch = reMatch("(?:se|sel|mkp)(\\d+)", cleanQuery)
        if (seMatch != null) {
            val room = rooms.find { it.id == "se_lab_$seMatch" }
            if (room != null) return room
        }

        // 5. Database Lab / Pangkalan Data: BM (MPD1..MPD3) & EN (DB1..DB3, DBL1..DBL3)
        val dbMatch = reMatch("(?:db|dbl|mpd)(\\d+)", cleanQuery)
        if (dbMatch != null) {
            val room = rooms.find { it.id == "db_lab_$dbMatch" }
            if (room != null) return room
        }

        // 6. Multimedia Lab: BM & EN (MM1..MM4, MML1..MML4)
        val mmMatch = reMatch("(?:mm|mml)(\\d+)", cleanQuery)
        if (mmMatch != null) {
            val room = rooms.find { it.id == "multimedia_lab_$mmMatch" }
            if (room != null) return room
        }

        // 7. Network Lab / Rangkaian: BM (MR1, MR2) & EN (NET1, NET2, NL1, NL2)
        val netMatch = reMatch("(?:net|nl|mr)(\\d+)", cleanQuery)
        if (netMatch != null) {
            val room = rooms.find { it.id == "net_lab_$netMatch" }
            if (room != null) return room
        }

        // 8. Meeting & Discussion Room Shortcuts (BM & EN)
        if (cleanQuery.contains("bmu") || cleanQuery.contains("mmr") || cleanQuery.contains("mainmeeting")) {
            return rooms.find { it.id == "main_meeting_room" }
        }
        if (cleanQuery.contains("ds") || cleanQuery.contains("sh") || cleanQuery.contains("seminarhall") || cleanQuery.contains("dewanseminar")) {
            return rooms.find { it.id == "seminar_hall" }
        }
        if (cleanQuery.contains("bb") || cleanQuery.contains("dr") || cleanQuery.contains("discussion")) {
            return rooms.find { it.id == "discussion_room" || it.id == "admin_discussion" }
        }

        // 9. Full Name & Keyword Matching Fallback
        val rawClean = query.lowercase().trim()
        return rooms.find { room ->
            val nameMalayClean = room.nameMalay.lowercase().replace("\\s+".toRegex(), "")
            val nameEnglishClean = room.nameEnglish.lowercase().replace("\\s+".toRegex(), "")

            cleanQuery.contains(nameMalayClean) ||
            cleanQuery.contains(nameEnglishClean) ||
            nameMalayClean.contains(cleanQuery) ||
            nameEnglishClean.contains(cleanQuery) ||
            rawClean.contains(room.nameMalay.lowercase()) ||
            rawClean.contains(room.nameEnglish.lowercase()) ||
            room.nameMalay.lowercase().contains(rawClean) ||
            room.nameEnglish.lowercase().contains(rawClean)
        }
    }

    private fun reMatch(pattern: String, text: String): String? {
        val regex = Regex(pattern)
        val match = regex.find(text)
        return match?.groupValues?.getOrNull(1)
    }
}
