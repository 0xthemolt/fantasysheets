import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://hhcuqhvmzwmehdsaamhn.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhoY3VxaHZtendtZWhkc2FhbWhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ5NzIwMTIsImV4cCI6MjA1MDU0ODAxMn0.xJNGoFLnpnmQGLj8RY'

export default async function handler(req, res) {
  const { heroHandle } = req.query
  const supabase = createClient(supabaseUrl, supabaseKey)
  
  try {
    const { data, error } = await supabase
      .from('trades')
      .select('hero_id,hero_handle,rarity,card_picture,timestamp,buyer,seller,price,hero_rarity_trade_history_rank')
      .eq('hero_handle', heroHandle)
      .neq('buyer', '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841')
      .gte('timestamp', new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString())
      // ... rest of your query
    
    if (error) throw error
    res.status(200).json(data)
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
}