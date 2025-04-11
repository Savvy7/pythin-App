
DROP TABLE IF EXISTS `games`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `games` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` text NOT NULL,
  `igdb_id` int DEFAULT NULL,
  `cover` text,
  `release_date` text,
  `platforms` json DEFAULT NULL,
  `genres` json DEFAULT NULL,
  `rating` int DEFAULT NULL,
  `summary` text,
  `metadata` json DEFAULT NULL,
  `developer` text,
  `publisher` text,
  `tags` json DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;        
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `local_games`
--

DROP TABLE IF EXISTS `local_games`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `local_games` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` text NOT NULL,
  `igdb_id` int DEFAULT NULL,
  `cover` text,
  `release_date` text,
  `platforms` json DEFAULT NULL,
  `genres` json DEFAULT NULL,
  `rating` int DEFAULT NULL,
  `summary` text,
  `metadata` json DEFAULT NULL,
  `developer` text,
  `publisher` text,
  `game_modes` json DEFAULT NULL,
  `series` json DEFAULT NULL,
  `franchises` json DEFAULT NULL,
  `themes` json DEFAULT NULL,
  `game_engines` json DEFAULT NULL,
  `tags` json DEFAULT NULL,
  `weighted_rating` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `igdb_id` (`igdb_id`)
) ENGINE=InnoDB AUTO_INCREMENT=109 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;       
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_tracked_games`
--

DROP TABLE IF EXISTS `user_tracked_games`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_tracked_games` (
  `user_id` int NOT NULL,
  `game_igdb_id` int NOT NULL,
  `status` varchar(20) DEFAULT 'Wishlist',
  `personal_rating` int DEFAULT NULL,
  `date_added` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`game_igdb_id`),
  KEY `game_igdb_id` (`game_igdb_id`),
  CONSTRAINT `user_tracked_games_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `user_tracked_games_ibfk_2` FOREIGN KEY (`game_igdb_id`) REFERENCES `local_games` (`igdb_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` text NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
