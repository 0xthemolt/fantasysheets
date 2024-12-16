import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const CardOptimizer = () => {
  const [cards, setCards] = useState([]);
  const [selectedCards, setSelectedCards] = useState([]);

  // Function to add a new card
  const addCard = () => {
    const newCard = {
      id: cards.length + 1,
      projectedScore: Math.floor(Math.random() * 100),
      stars: Math.floor(Math.random() * 5) + 1
    };
    setCards([...cards, newCard]);
  };

  // Function to find optimal combination
  const findOptimalCombination = () => {
    const n = cards.length;
    const targetCount = 5;
    const maxStars = 18;
    let bestScore = 0;
    let bestCombo = [];
    
    // Helper function to get combinations
    const getCombinations = (arr, size) => {
      const result = [];
      
      function combine(start, combo) {
        if (combo.length === size) {
          const totalStars = combo.reduce((sum, card) => sum + card.stars, 0);
          if (totalStars < maxStars) {
            const totalScore = combo.reduce((sum, card) => sum + card.projectedScore, 0);
            if (totalScore > bestScore) {
              bestScore = totalScore;
              bestCombo = [...combo];
            }
          }
          return;
        }
        
        for (let i = start; i < arr.length; i++) {
          combine(i + 1, [...combo, arr[i]]);
        }
      }
      
      combine(0, []);
      return result;
    };

    getCombinations(cards, targetCount);
    setSelectedCards(bestCombo);
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Card Selection Optimizer</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex gap-4">
            <Button 
              onClick={addCard}
              className="bg-blue-500 hover:bg-blue-600"
            >
              Add Random Card
            </Button>
            <Button 
              onClick={findOptimalCombination}
              className="bg-green-500 hover:bg-green-600"
              disabled={cards.length < 5}
            >
              Find Best Combination
            </Button>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <h3 className="text-lg font-semibold mb-2">Available Cards ({cards.length})</h3>
              <div className="space-y-2">
                {cards.map(card => (
                  <div 
                    key={card.id} 
                    className="p-2 border rounded bg-gray-50"
                  >
                    Card {card.id}: Score {card.projectedScore}, Stars {card.stars}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-2">Optimal Selection</h3>
              <div className="space-y-2">
                {selectedCards.map(card => (
                  <div 
                    key={card.id} 
                    className="p-2 border rounded bg-green-50"
                  >
                    Card {card.id}: Score {card.projectedScore}, Stars {card.stars}
                  </div>
                ))}
                {selectedCards.length > 0 && (
                  <div className="mt-4 p-2 border rounded bg-blue-50">
                    Total Score: {selectedCards.reduce((sum, card) => sum + card.projectedScore, 0)}
                    <br />
                    Total Stars: {selectedCards.reduce((sum, card) => sum + card.stars, 0)}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default CardOptimizer;