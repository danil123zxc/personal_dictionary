-- Add hash indexes on words table lemma field
-- This script adds hash indexes for better performance on exact equality comparisons

-- Hash index on lemma field
-- More efficient than B-tree for exact string equality comparisons
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_words_lemma_hash 
ON words USING hash (lemma);

-- Composite hash index for lemma + language_id
-- Useful for queries that filter by both lemma and language
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_words_lemma_language_hash 
ON words USING hash (lemma, language_id);

-- Functional hash index for lowercase lemma
-- Useful for case-insensitive searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_words_lemma_lower_hash 
ON words USING hash (LOWER(lemma));

-- Add comments to document the indexes
COMMENT ON INDEX idx_words_lemma_hash IS 'Hash index on lemma field for exact equality comparisons';
COMMENT ON INDEX idx_words_lemma_language_hash IS 'Composite hash index on lemma and language_id for filtered queries';
COMMENT ON INDEX idx_words_lemma_lower_hash IS 'Functional hash index on lowercase lemma for case-insensitive searches';

-- Show the created indexes
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'words' 
AND indexname LIKE '%hash%'
ORDER BY indexname;
