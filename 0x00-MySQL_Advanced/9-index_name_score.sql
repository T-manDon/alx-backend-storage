-- Creat index idx_name_first_score on table names and
-- the first letter of name n score.
CREATE INDEX idx_name_first_score ON names(name(1), score);
