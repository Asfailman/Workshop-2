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
        // Blok A: rect M170,45 h60 v35 — center (200,62). c_act=left half, lobi=right half
        FtmkRoom("c_act", "C-ACT", "C-ACT", "Blok A", 1, "Administrative", 0.46f, 0.21f),
        FtmkRoom("lobi", "Lobi", "Lobby", "Blok A", 1, "Administrative", 0.54f, 0.21f),
        // Blok C1: arm M45,210 L125,100 L145,115 L65,225 — top(135,107)→bot(55,217), rooms top→bottom
        FtmkRoom("vr_studio_1", "Studio Realiti Maya", "Virtual Reality Studio", "Blok C1", 1, "Studio", 0.33f, 0.38f),
        FtmkRoom("bk14", "Bilik Kuliah 14", "Lecture Room 14", "Blok C1", 1, "Lecture Room", 0.29f, 0.44f),
        FtmkRoom("students_common", "Bilik Umum Pelajar", "Students' Common Room", "Blok C1", 1, "Common Area", 0.26f, 0.50f),
        FtmkRoom("bk12", "Bilik Kuliah 12", "Lecture Room 12", "Blok C1", 1, "Lecture Room", 0.23f, 0.56f),
        FtmkRoom("bk11", "Bilik Kuliah 11", "Lecture Room 11", "Blok C1", 1, "Lecture Room", 0.20f, 0.62f),
        FtmkRoom("bk9_10", "Bilik Kuliah 9 & 10", "Lecture Room 9 & 10", "Blok C1", 1, "Lecture Room", 0.16f, 0.68f),
        // Blok C2: arm M100,240 L160,150 L180,165 L120,255 — top(170,157)→bot(110,247), rooms top→bottom
        FtmkRoom("esport_lab", "Makmal e-Sport", "e-Sport Lab", "Blok C2", 1, "Lab", 0.40f, 0.57f),
        FtmkRoom("bk13", "Bilik Kuliah 13", "Lecture Room 13", "Blok C2", 1, "Lecture Room", 0.35f, 0.68f),
        FtmkRoom("mtds_lab", "Makmal MTDS", "MTDS Lab", "Blok C2", 1, "Lab", 0.30f, 0.78f),
        // Blok E1: arm M275,100 L355,210 L335,225 L255,115 — top(265,107)→bot(345,217), rooms top→bottom
        FtmkRoom("se_lab_1", "Makmal Kejuruteraan Perisian 1", "Software Engineering Lab 1", "Blok E1", 1, "Lab", 0.67f, 0.38f),
        FtmkRoom("se_lab_2", "Makmal Kejuruteraan Perisian 2", "Software Engineering Lab 2", "Blok E1", 1, "Lab", 0.70f, 0.43f),
        FtmkRoom("se_lab_3", "Makmal Kejuruteraan Perisian 3", "Software Engineering Lab 3", "Blok E1", 1, "Lab", 0.73f, 0.48f),
        FtmkRoom("bk5", "Bilik Kuliah 5", "Lecture Room 5", "Blok E1", 1, "Lecture Room", 0.76f, 0.53f),
        FtmkRoom("bk4", "Bilik Kuliah 4", "Lecture Room 4", "Blok E1", 1, "Lecture Room", 0.78f, 0.58f),
        FtmkRoom("bk3", "Bilik Kuliah 3", "Lecture Room 3", "Blok E1", 1, "Lecture Room", 0.81f, 0.63f),
        FtmkRoom("bk2", "Bilik Kuliah 2", "Lecture Room 2", "Blok E1", 1, "Lecture Room", 0.83f, 0.67f),
        FtmkRoom("bk1", "Bilik Kuliah 1", "Lecture Room 1", "Blok E1", 1, "Lecture Room", 0.86f, 0.71f),
        // Blok E2: arm M240,150 L300,240 L280,255 L220,165 — top(230,157)→bot(290,247), rooms top→bottom
        FtmkRoom("bk6", "Bilik Kuliah 6", "Lecture Room 6", "Blok E2", 1, "Lecture Room", 0.59f, 0.55f),
        FtmkRoom("bk7", "Bilik Kuliah 7", "Lecture Room 7", "Blok E2", 1, "Lecture Room", 0.61f, 0.60f),
        FtmkRoom("bk8", "Bilik Kuliah 8", "Lecture Room 8", "Blok E2", 1, "Lecture Room", 0.64f, 0.65f),
        FtmkRoom("prog_lab_1", "Makmal Pengaturcaraan 1", "Programming Lab 1", "Blok E2", 1, "Lab", 0.66f, 0.69f),
        FtmkRoom("prog_lab_2", "Makmal Pengaturcaraan 2", "Programming Lab 2", "Blok E2", 1, "Lab", 0.68f, 0.74f),
        FtmkRoom("biocore_lab", "Makmal Penyelidikan BIOCORE", "BIOCORE Research Lab", "Blok E2", 1, "Research Lab", 0.70f, 0.77f),
        FtmkRoom("optimass_lab", "Makmal Penyelidikan OPTIMASS", "OPTIMASS Research Lab", "Blok E2", 1, "Research Lab", 0.72f, 0.81f),

        // LEVEL 2 (ARAS 2) — same block geometry as Level 1
        FtmkRoom("discussion_room", "Bilik Bincang", "Discussion Room", "Blok A", 2, "Meeting", 0.50f, 0.21f),
        // Blok C1 rooms, top→bottom
        FtmkRoom("clear_room", "Bilik CLeaR FTMK", "FTMK CLeaR Room", "Blok C1", 2, "Special Room", 0.32f, 0.40f),
        FtmkRoom("game_lab", "Makmal Permainan Komputer", "Computer Games Lab", "Blok C1", 2, "Lab", 0.28f, 0.46f),
        FtmkRoom("multimedia_lab_2", "Makmal Multimedia 2", "Multimedia Lab 2", "Blok C1", 2, "Lab", 0.24f, 0.54f),
        FtmkRoom("multimedia_lab_1", "Makmal Multimedia 1", "Multimedia Lab 1", "Blok C1", 2, "Lab", 0.19f, 0.62f),
        // Blok C2 rooms
        FtmkRoom("cybersecurity_center", "Cybersecurity Competence Center", "Cybersecurity Center", "Blok C2", 2, "Center", 0.40f, 0.57f),
        FtmkRoom("ccna_ccnp_lab", "Makmal CCNA & CCNP", "CCNA & CCNP Lab", "Blok C2", 2, "Lab", 0.35f, 0.68f),
        FtmkRoom("fiber_optic_lab", "Makmal Fiber Optic", "Fiber Optic Lab", "Blok C2", 2, "Lab", 0.30f, 0.78f),
        // Blok E1 rooms
        FtmkRoom("db_lab_3", "Makmal Pangkalan Data 3", "Database Lab 3", "Blok E1", 2, "Lab", 0.68f, 0.40f),
        FtmkRoom("db_lab_2", "Makmal Pangkalan Data 2", "Database Lab 2", "Blok E1", 2, "Lab", 0.72f, 0.46f),
        FtmkRoom("db_lab_1", "Makmal Pangkalan Data 1", "Database Lab 1", "Blok E1", 2, "Lab", 0.76f, 0.53f),
        FtmkRoom("net_lab_2", "Makmal Rangkaian 2", "Network Lab 2", "Blok E1", 2, "Lab", 0.79f, 0.59f),
        FtmkRoom("pet_lab", "Makmal Penyelidikan PET", "PET Research Lab", "Blok E1", 2, "Research Lab", 0.82f, 0.64f),
        // Blok E2 rooms
        FtmkRoom("ai_lab_3", "Makmal Kepintaran Buatan 3", "Artificial Intelligence Lab 3", "Blok E2", 2, "Lab", 0.59f, 0.56f),
        FtmkRoom("ai_lab_1", "Makmal Kepintaran Buatan 1", "Artificial Intelligence Lab 1", "Blok E2", 2, "Lab", 0.62f, 0.61f),
        FtmkRoom("ai_lab_2", "Makmal Kepintaran Buatan 2", "Artificial Intelligence Lab 2", "Blok E2", 2, "Lab", 0.64f, 0.66f),
        FtmkRoom("recap_room", "Bilik ReCap", "ReCap Room", "Blok E2", 2, "Special Room", 0.67f, 0.72f),
        FtmkRoom("ai_lab_4", "Makmal Kepintaran Buatan 4", "Artificial Intelligence Lab 4", "Blok E2", 2, "Lab", 0.70f, 0.77f),

        // LEVEL 3 (ARAS 3) — same block geometry
        FtmkRoom("admin_discussion", "Bilik Bincang Pentadbiran", "Administrative Discussion Room", "Blok A", 3, "Administrative", 0.50f, 0.21f),
        // Blok C1 rooms
        FtmkRoom("multimedia_lab_4", "Makmal Multimedia 4", "Multimedia Lab 4", "Blok C1", 3, "Lab", 0.32f, 0.39f),
        FtmkRoom("vr_lab", "Makmal Realiti Maya", "Virtual Reality Lab", "Blok C1", 3, "Lab", 0.29f, 0.44f),
        FtmkRoom("multimedia_lab_3", "Makmal Multimedia 3", "Multimedia Lab 3", "Blok C1", 3, "Lab", 0.26f, 0.49f),
        FtmkRoom("mini_theatre", "Studio Multimedia (Teater Mini)", "Multimedia Studio (Mini Theatre)", "Blok C1", 3, "Studio", 0.24f, 0.55f),
        FtmkRoom("audio_room_1", "Bilik Rakaman Audio 1", "Audio Recording Room 1", "Blok C1", 3, "Studio", 0.21f, 0.59f),
        FtmkRoom("audio_room_2", "Bilik Rakaman Audio 2", "Audio Recording Room 2", "Blok C1", 3, "Studio", 0.19f, 0.63f),
        FtmkRoom("shooting_studio", "Studio Pengambaran", "Shooting Studio", "Blok C1", 3, "Studio", 0.16f, 0.68f),
        // Blok C2 rooms
        FtmkRoom("huawei_lab", "Makmal Huawei", "Huawei Lab", "Blok C2", 3, "Lab", 0.40f, 0.57f),
        FtmkRoom("security_lab_2", "Makmal Keselamatan 2", "Security Lab 2", "Blok C2", 3, "Lab", 0.35f, 0.68f),
        FtmkRoom("wireless_lab", "Makmal Tanpa Wayar", "Wireless Lab", "Blok C2", 3, "Lab", 0.30f, 0.78f),
        // Blok E1 rooms
        FtmkRoom("systems_hardware_lab", "Makmal Sistem dan Perkakasan", "Systems and Hardware Lab", "Blok E1", 3, "Lab", 0.68f, 0.40f),
        FtmkRoom("systems_lab", "Makmal Sistem", "Systems Lab", "Blok E1", 3, "Lab", 0.72f, 0.46f),
        FtmkRoom("net_lab_1", "Makmal Rangkaian 1", "Network Lab 1", "Blok E1", 3, "Lab", 0.76f, 0.53f),
        FtmkRoom("exec_lab", "Makmal Eksekutif", "Executive Lab", "Blok E1", 3, "Lab", 0.79f, 0.59f),
        FtmkRoom("students_workshop", "Bengkel Pelajar", "Students' Workshop", "Blok E1", 3, "Workshop", 0.82f, 0.64f),
        // Blok E2 rooms
        FtmkRoom("skk_workshop", "Bengkel SKK", "SKK Workshop", "Blok E2", 3, "Workshop", 0.59f, 0.55f),
        FtmkRoom("robotics_lab", "Makmal Robotik", "Robotics Lab", "Blok E2", 3, "Lab", 0.61f, 0.60f),
        FtmkRoom("biti_workshop", "Bengkel BITI", "BITI Workshop", "Blok E2", 3, "Workshop", 0.64f, 0.65f),
        FtmkRoom("cmerp_lab", "Makmal CMERP", "CMERP Lab", "Blok E2", 3, "Lab", 0.66f, 0.69f),
        FtmkRoom("ideal_lab", "Makmal Penyelidikan IDEAL", "IDEAL Research Lab", "Blok E2", 3, "Research Lab", 0.68f, 0.74f),
        FtmkRoom("is3_lab", "Makmal Penyelidikan IS3", "IS3 Research Lab", "Blok E2", 3, "Research Lab", 0.71f, 0.79f),

        // LEVEL 4 (ARAS 4)
        FtmkRoom("seminar_hall", "Dewan Seminar", "Seminar Hall", "Blok A", 4, "Hall", 0.46f, 0.21f),
        FtmkRoom("main_meeting_room", "Bilik Mesyuarat Utama", "Main Meeting Room", "Blok A", 4, "Meeting", 0.54f, 0.21f),
        // Blok E1 rooms (Level 4 only has a few)
        FtmkRoom("prog_lab_3", "Makmal Pengaturcaraan 3", "Programming Lab 3", "Blok E1", 4, "Lab", 0.70f, 0.43f),
        FtmkRoom("prog_lab_4", "Makmal Pengaturcaraan 4", "Programming Lab 4", "Blok E1", 4, "Lab", 0.76f, 0.54f),
        FtmkRoom("bitd_workshop", "Bengkel BITD", "BITD Workshop", "Blok E1", 4, "Workshop", 0.82f, 0.65f),
        // Blok E2 rooms
        FtmkRoom("advit_lab", "Makmal Penyelidikan AdViT", "AdViT Research Lab", "Blok E2", 4, "Research Lab", 0.62f, 0.62f),
        FtmkRoom("inforsnet_lab", "Makmal Penyelidikan INFORSNET", "INFORSNET Research Lab", "Blok E2", 4, "Research Lab", 0.68f, 0.74f)
    )

    // Direct mapping from Backend Repository IDs to Android Room IDs
    val backendIdToRoomId = mapOf(
        // Block A
        "MAIN_ENTRANCE" to "lobi",
        "B_A_L1_C_ACT" to "c_act",
        "B_A_L2_DISCUSSION_ROOM" to "discussion_room",
        "B_A_L3_ADMINISTRATIVE_DISCUSSION_ROOM" to "admin_discussion",
        "B_A_L4_SEMINAR_HALL" to "seminar_hall",
        "B_A_L4_MAIN_MEETING_ROOM" to "main_meeting_room",

        // Programming Labs
        "B_B_L1_PROGRAMMING_LAB_1" to "prog_lab_1",
        "B_B_L1_PROGRAMMING_LAB_2" to "prog_lab_2",
        "B_C_L4_PROGRAMMING_LAB_3" to "prog_lab_3",
        "B_C_L4_PROGRAMMING_LAB_4" to "prog_lab_4",

        // AI Labs
        "B_B_L2_AI_LAB_1" to "ai_lab_1",
        "B_B_L2_AI_LAB_2" to "ai_lab_2",
        "B_B_L2_AI_LAB_3" to "ai_lab_3",
        "B_B_L2_AI_LAB_4" to "ai_lab_4",

        // Software Engineering Labs
        "B_C_L1_SOFTWARE_ENGINEERING_LAB_1" to "se_lab_1",
        "B_C_L1_SOFTWARE_ENGINEERING_LAB_2" to "se_lab_2",
        "B_C_L1_SOFTWARE_ENGINEERING_LAB_3" to "se_lab_3",

        // Database Labs
        "B_C_L2_DATABASE_LAB_1" to "db_lab_1",
        "B_C_L2_DATABASE_LAB_2" to "db_lab_2",
        "B_C_L2_DATABASE_LAB_3" to "db_lab_3",

        // Multimedia Labs
        "B_D_L2_MULTIMEDIA_LAB_1" to "multimedia_lab_1",
        "B_D_L2_MULTIMEDIA_LAB_2" to "multimedia_lab_2",
        "B_D_L3_MULTIMEDIA_LAB_3" to "multimedia_lab_3",
        "B_D_L3_MULTIMEDIA_LAB_4" to "multimedia_lab_4",

        // Network Labs
        "B_C_L3_NETWORK_LAB_1" to "net_lab_1",
        "B_C_L2_NETWORK_LAB_2" to "net_lab_2",

        // Lecture Rooms (BK)
        "B_C_L1_BK_1" to "bk1",
        "B_C_L1_BK_2" to "bk2",
        "B_C_L1_BK_3" to "bk3",
        "B_C_L1_BK_4" to "bk4",
        "B_C_L1_BK_5" to "bk5",
        "B_B_L1_BK_6" to "bk6",
        "B_B_L1_BK_7" to "bk7",
        "B_E_L1_BK_13" to "bk13",
        "B_D_L1_BK_14" to "bk14",
        "B_B_L3_BK_15" to "bk15",
        "B_B_L4_BK_16" to "bk16",

        // Other Facilities
        "B_B_L3_ROBOTICS_LAB" to "robotics_lab",
        "B_D_L3_VR_LAB" to "vr_lab",
        "B_D_L1_METAVERSE_STUDIO" to "vr_studio_1",
        "B_D_L1_STUDENTS_COMMON_ROOM" to "students_common",
        "B_E_L1_GAME_ARENA" to "esport_lab",
        "B_E_L2_CYBERSECURITY_COMPETENCE_CENTER" to "cybersecurity_center",
        "B_E_L2_CCNA_CCNP_LAB" to "ccna_ccnp_lab",
        "B_E_L2_FIBER_OPTIC_LAB" to "fiber_optic_lab",
        "B_E_L3_WIRELESS_LAB" to "wireless_lab",
        "B_E_L3_SECURITY_LAB_2" to "security_lab_2",
        "B_C_L3_SYSTEMS_HARDWARE_LAB" to "systems_hardware_lab",
        "B_C_L3_SYSTEMS_LAB" to "systems_lab",
        "B_B_L3_BITI_WORKSHOP" to "biti_workshop",
        "B_B_L3_SKK_WORKSHOP" to "skk_workshop",
        "B_C_L4_BITD_WORKSHOP" to "bitd_workshop",
        "B_D_L3_AUDIO_RECORDING_ROOM_1" to "audio_room_1",
        "B_D_L3_AUDIO_RECORDING_ROOM_2" to "audio_room_2",
        "B_D_L3_MINI_THEATRE" to "mini_theatre"
    )

    fun findRoomById(id: String?): FtmkRoom? {
        if (id.isNullOrBlank()) return null
        val direct = rooms.find { it.id.equals(id, ignoreCase = true) }
        if (direct != null) return direct

        val mappedId = backendIdToRoomId[id] ?: backendIdToRoomId[id.uppercase()]
        if (mappedId != null) {
            val mappedRoom = rooms.find { it.id.equals(mappedId, ignoreCase = true) }
            if (mappedRoom != null) return mappedRoom
        }

        // Fuzzy fallback for IDs
        val clean = id.lowercase()
        return when {
            clean.contains("prog") && clean.contains("1") -> rooms.find { it.id == "prog_lab_1" }
            clean.contains("prog") && clean.contains("2") -> rooms.find { it.id == "prog_lab_2" }
            clean.contains("prog") && clean.contains("3") -> rooms.find { it.id == "prog_lab_3" }
            clean.contains("prog") && clean.contains("4") -> rooms.find { it.id == "prog_lab_4" }
            clean.contains("ai") && clean.contains("1") -> rooms.find { it.id == "ai_lab_1" }
            clean.contains("ai") && clean.contains("2") -> rooms.find { it.id == "ai_lab_2" }
            clean.contains("ai") && clean.contains("3") -> rooms.find { it.id == "ai_lab_3" }
            clean.contains("ai") && clean.contains("4") -> rooms.find { it.id == "ai_lab_4" }
            clean.contains("se_lab") || clean.contains("software") -> {
                val num = Regex("\\d+").find(clean)?.value ?: "1"
                rooms.find { it.id == "se_lab_$num" }
            }
            clean.contains("db_lab") || clean.contains("database") -> {
                val num = Regex("\\d+").find(clean)?.value ?: "1"
                rooms.find { it.id == "db_lab_$num" }
            }
            clean.contains("multimedia") -> {
                val num = Regex("\\d+").find(clean)?.value ?: "1"
                rooms.find { it.id == "multimedia_lab_$num" }
            }
            clean.contains("network") || clean.contains("net_lab") -> {
                val num = Regex("\\d+").find(clean)?.value ?: "1"
                rooms.find { it.id == "net_lab_$num" }
            }
            clean.contains("bk") -> {
                val num = Regex("\\d+").find(clean)?.value
                rooms.find { it.id == "bk$num" }
            }
            clean.contains("entrance") || clean.contains("lobby") -> rooms.find { it.id == "lobi" }
            clean.contains("c_act") -> rooms.find { it.id == "c_act" }
            clean.contains("seminar") -> rooms.find { it.id == "seminar_hall" }
            clean.contains("meeting") -> rooms.find { it.id == "main_meeting_room" }
            clean.contains("discussion") -> rooms.find { it.id == "discussion_room" }
            else -> null
        }
    }

    fun findRoomByQuery(query: String?): FtmkRoom? {
        if (query.isNullOrBlank()) return null
        val clean = query.lowercase().trim()

        // 1. Programming Lab (matches "program lab 1", "programming lab", "prog lab 1", "pl 1", "makmal pengaturcaraan")
        val progMatch = Regex("\\b(?:prog(?:ram(?:ming)?)?|pengaturcaraan|mp|pl)\\s*(?:lab(?:oratory)?|makmal)?(?:\\s*([1-4]))?\\b", RegexOption.IGNORE_CASE).find(clean)
        if (progMatch != null && (clean.contains("lab") || clean.contains("makmal") || clean.contains("prog") || clean.contains("pengaturcaraan"))) {
            val num = progMatch.groupValues[1].ifEmpty { "1" }
            val room = rooms.find { it.id == "prog_lab_$num" }
            if (room != null) return room
        }

        // 2. Artificial Intelligence Lab (matches "ai lab 1", "ai lab", "artificial intelligence lab")
        val aiMatch = Regex("\\b(?:ai|mkb|kepintaran\\s*buatan|artificial\\s*intelligence)\\s*(?:lab(?:oratory)?|makmal)?(?:\\s*([1-4]))?\\b", RegexOption.IGNORE_CASE).find(clean)
        if (aiMatch != null && (clean.contains("lab") || clean.contains("makmal") || clean.contains("ai") || clean.contains("kepintaran") || clean.contains("artificial"))) {
            val num = aiMatch.groupValues[1].ifEmpty { "1" }
            val room = rooms.find { it.id == "ai_lab_$num" }
            if (room != null) return room
        }

        // 3. Software Engineering Lab (matches "se lab 1", "software lab", "software engineering lab")
        val seMatch = Regex("\\b(?:soft(?:ware)?(?:\\s*eng(?:ineering)?)?|se|sel|mkp|kejuruteraan\\s*perisian)\\s*(?:lab(?:oratory)?|makmal)?(?:\\s*([1-3]))?\\b", RegexOption.IGNORE_CASE).find(clean)
        if (seMatch != null && (clean.contains("lab") || clean.contains("makmal") || clean.contains("soft") || clean.contains("perisian") || clean.contains("se"))) {
            val num = seMatch.groupValues[1].ifEmpty { "1" }
            val room = rooms.find { it.id == "se_lab_$num" }
            if (room != null) return room
        }

        // 4. Database Lab (matches "db lab 1", "database lab", "pangkalan data")
        val dbMatch = Regex("\\b(?:data(?:base)?|db|dbl|mpd|pangkalan\\s*data)\\s*(?:lab(?:oratory)?|makmal)?(?:\\s*([1-3]))?\\b", RegexOption.IGNORE_CASE).find(clean)
        if (dbMatch != null && (clean.contains("lab") || clean.contains("makmal") || clean.contains("data") || clean.contains("db"))) {
            val num = dbMatch.groupValues[1].ifEmpty { "1" }
            val room = rooms.find { it.id == "db_lab_$num" }
            if (room != null) return room
        }

        // 5. Multimedia Lab (matches "multimedia lab 1", "mm lab", "multimedia lab")
        val mmMatch = Regex("\\b(?:multi(?:media)?|mm|mml)\\s*(?:lab(?:oratory)?|makmal)?(?:\\s*([1-4]))?\\b", RegexOption.IGNORE_CASE).find(clean)
        if (mmMatch != null && (clean.contains("lab") || clean.contains("makmal") || clean.contains("multi") || clean.contains("mm"))) {
            val num = mmMatch.groupValues[1].ifEmpty { "1" }
            val room = rooms.find { it.id == "multimedia_lab_$num" }
            if (room != null) return room
        }

        // 6. Network Lab (matches "network lab 1", "net lab", "network lab")
        val netMatch = Regex("\\b(?:net(?:work(?:ing)?)?|nl|mr|rangkaian)\\s*(?:lab(?:oratory)?|makmal)?(?:\\s*([1-2]))?\\b", RegexOption.IGNORE_CASE).find(clean)
        if (netMatch != null && (clean.contains("lab") || clean.contains("makmal") || clean.contains("net") || clean.contains("rangkaian"))) {
            val num = netMatch.groupValues[1].ifEmpty { "1" }
            val room = rooms.find { it.id == "net_lab_$num" }
            if (room != null) return room
        }

        // 7. Lecture Room / Bilik Kuliah (matches "bk 1", "bk1", "lecture room 1", "bilik kuliah 1", "lr 1")
        val bkMatch = Regex("\\b(?:bilik\\s*kuliah|lec(?:ture)?\\s*room|bk|lr)\\s*([0-9]{1,2})\\b", RegexOption.IGNORE_CASE).find(clean)
        if (bkMatch != null) {
            val num = bkMatch.groupValues[1]
            val room = rooms.find { it.id == "bk$num" || it.id == "bk${num}_10" }
            if (room != null) return room
        }

        // 8. Specific facilities by exact word boundary
        if (Regex("\\b(bmu|mmr|main\\s*meeting(?:\\s*room)?|bilik\\s*mesyuarat\\s*utama)\\b", RegexOption.IGNORE_CASE).containsMatchIn(clean)) {
            return rooms.find { it.id == "main_meeting_room" }
        }
        if (Regex("\\b(dewan\\s*seminar|seminar\\s*hall|exam\\s*hall)\\b", RegexOption.IGNORE_CASE).containsMatchIn(clean)) {
            return rooms.find { it.id == "seminar_hall" }
        }
        if (Regex("\\b(bilik\\s*bincang|discussion\\s*room)\\b", RegexOption.IGNORE_CASE).containsMatchIn(clean)) {
            return rooms.find { it.id == "discussion_room" }
        }
        if (Regex("\\b(c-?act|bilik\\s*c-?act)\\b", RegexOption.IGNORE_CASE).containsMatchIn(clean)) {
            return rooms.find { it.id == "c_act" }
        }
        if (Regex("\\b(lobi|lobby|main\\s*entrance|pintu\\s*masuk)\\b", RegexOption.IGNORE_CASE).containsMatchIn(clean)) {
            return rooms.find { it.id == "lobi" }
        }
        if (Regex("\\b(bilik\\s*umum(?:\\s*pelajar)?|students?\\s*common\\s*room)\\b", RegexOption.IGNORE_CASE).containsMatchIn(clean)) {
            return rooms.find { it.id == "students_common" }
        }
        if (Regex("\\b(robot(?:ics)?\\s*lab|makmal\\s*robotik)\\b", RegexOption.IGNORE_CASE).containsMatchIn(clean)) {
            return rooms.find { it.id == "robotics_lab" }
        }
        if (Regex("\\b(vr\\s*lab|makmal\\s*realiti\\s*maya|virtual\\s*reality\\s*lab)\\b", RegexOption.IGNORE_CASE).containsMatchIn(clean)) {
            return rooms.find { it.id == "vr_lab" }
        }
        if (Regex("\\b(game(?:s)?\\s*lab|e-?sports?\\s*lab|arena\\s*permainan)\\b", RegexOption.IGNORE_CASE).containsMatchIn(clean)) {
            return rooms.find { it.id == "esport_lab" }
        }

        // 9. Full Name Matching Fallback (requires at least 4 characters to avoid false matches)
        return rooms.find { room ->
            val ml = room.nameMalay.lowercase()
            val en = room.nameEnglish.lowercase()
            (clean.contains(ml) && ml.length >= 4) ||
            (clean.contains(en) && en.length >= 4) ||
            (clean.length >= 4 && (ml.contains(clean) || en.contains(clean)))
        }
    }

    /**
     * Comprehensive resolver prioritizing backend destination ID, extracted entity, then user query.
     */
    fun findRoom(backendId: String? = null, entityName: String? = null, query: String? = null): FtmkRoom? {
        val byId = findRoomById(backendId)
        if (byId != null) return byId

        val byEntity = findRoomByQuery(entityName)
        if (byEntity != null) return byEntity

        return findRoomByQuery(query)
    }
}
