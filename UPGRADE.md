Here is a list of commits with db changes and what to do to upgrade

618661b3349bb809eb2f181511129420e7848e3e

PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE "main_document" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(200) NOT NULL,
    "file" varchar(100) NOT NULL,
    "upload_date" datetime NOT NULL,
    "hash" varchar(200) NOT NULL,
    "public" bool NOT NULL,
    "deleted" bool NOT NULL
);

PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE "main_section" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(200) NOT NULL,
    "index" integer NOT NULL,
    "summary_id" integer NOT NULL REFERENCES "main_summary" ("id"),
    "creation_date" datetime NOT NULL,
    "section" text NOT NULL,
    "deleted" bool NOT NULL
);
CREATE INDEX "main_section_94484ec1" ON "main_section" ("summary_id");

ALTER TABLE "main_document" ADD COLUMN "deleted" bool NOT NULL;
COMMIT;
