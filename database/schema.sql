-- Drop if exists
DROP DATABASE IF EXISTS who_dunnit_bro;
CREATE DATABASE who_dunnit_bro;
USE who_dunnit_bro;

-- Detectives Table
CREATE TABLE detectives (
    detective_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cases Table
CREATE TABLE cases (
    case_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    status ENUM('Open', 'Under Investigation', 'Solved') DEFAULT 'Open',
    detective_id INT,
    FOREIGN KEY (detective_id) REFERENCES detectives(detective_id) ON DELETE SET NULL
);

-- Clues Table
CREATE TABLE clues (
    clue_id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    description TEXT NOT NULL,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);

-- Suspects Table
CREATE TABLE suspects (
    suspect_id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    name VARCHAR(100) NOT NULL,
    evidence_score INT DEFAULT 0,
    remarks VARCHAR(255),
    is_guilty BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);

-- Stored Procedure: Update Evidence Score
DELIMITER //
CREATE PROCEDURE update_evidence(IN p_suspect_id INT, IN p_value INT)
BEGIN
    UPDATE suspects 
    SET evidence_score = evidence_score + p_value 
    WHERE suspect_id = p_suspect_id;
END //
DELIMITER ;

-- Insert Admin Detective (password: admin123)
INSERT INTO detectives (name, username, password) 
VALUES ('Admin Holmes', 'admin', '$2b$12$PfgYgrjE15g7I5XNvAf5Yub3hkNUdego3.LTIkX.uOYAD7LrEXnqu');

-- Insert Detective Watson (password: watson123)
INSERT INTO detectives (name, username, password) 
VALUES ('Detective Watson', 'watson', '$2b$12$Qmd.3MyLB4ljA.3OZAST4OiS2hkyyuS0daonXQItenBK.bCvPcSu2');

-- Insert Detective Lestrade (password: lestrade123)
INSERT INTO detectives (name, username, password) 
VALUES ('Detective Lestrade', 'lestrade', '$2b$12$cXPNSVLrO1tF/MxCvDnWMONA9132byyNIQE0AQkaQAHeLmXmKbQ4W');