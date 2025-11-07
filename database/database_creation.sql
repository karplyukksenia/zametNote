create database database_PKM

use database_PKM

CREATE TABLE users(
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    username NVARCHAR(255) NOT NULL UNIQUE,
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL
);

CREATE TABLE notes(
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_id INT NOT NULL,
    title NVARCHAR(255) NOT NULL,
    content NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
);

CREATE TABLE tags(
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_id INT NOT NULL,
    name NVARCHAR(255) NOT NULL,
    CONSTRAINT UQ_tags_user_name UNIQUE (user_id, name)
);

CREATE TABLE note_tags(
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    tag_id INT NOT NULL,
    note_id INT NOT NULL,
    CONSTRAINT UQ_note_tags_note_tag UNIQUE (note_id, tag_id)
);

CREATE TABLE note_links(
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    source_note_id INT NOT NULL,
    target_node_id INT NOT NULL,
    CONSTRAINT UQ_note_links_source_target UNIQUE (source_note_id, target_node_id)
);

ALTER TABLE notes ADD CONSTRAINT FK_notes_users 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE tags ADD CONSTRAINT FK_tags_users 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE note_tags ADD CONSTRAINT FK_note_tags_tag_id 
FOREIGN KEY (tag_id) REFERENCES tags(id);

ALTER TABLE note_tags ADD CONSTRAINT FK_note_tags_note_id 
FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE;

ALTER TABLE note_links ADD CONSTRAINT FK_note_links_source_note_id 
FOREIGN KEY (source_note_id) REFERENCES notes(id) ON DELETE CASCADE;

ALTER TABLE note_links ADD CONSTRAINT FK_note_links_target_node_id 
FOREIGN KEY (target_node_id) REFERENCES notes(id);