import React from 'react'
import CardOptimizer from './components/CardOptimizer'

function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Card Optimizer</h1>
        <CardOptimizer />
      </div>
    </div>
  )
}

export default App