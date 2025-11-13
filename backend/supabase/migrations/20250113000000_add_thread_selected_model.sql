-- Add selected_model column to threads table to store chat-specific model selection
ALTER TABLE threads ADD COLUMN IF NOT EXISTS selected_model TEXT;

-- Create index for model queries
CREATE INDEX IF NOT EXISTS idx_threads_selected_model ON threads(selected_model);

-- Comment on the column
COMMENT ON COLUMN threads.selected_model IS 'Model selected specifically for this chat thread. Takes priority over agent default model.';
