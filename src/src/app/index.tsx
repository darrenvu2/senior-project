
import { useState } from 'react';
import {
  ActivityIndicator,
  Button,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

const API_URL = 'http://127.0.0.1:8000';

export default function HomeScreen() {
  const [query, setQuery] = useState('');
  const [foods, setFoods] = useState<any[]>([]);
  const [selectedFood, setSelectedFood] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function searchFoods() {
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setFoods([]);
    setSelectedFood(null);

    try {
      const response = await fetch(
        `${API_URL}/foods/search?query=${encodeURIComponent(query)}`
      );

      if (!response.ok) {
        throw new Error('Food search failed');
      }

      const data = await response.json();
      setFoods(data.results || []);
    } catch {
      setError('Cannot connect to the food database.');
    } finally {
      setLoading(false);
    }
  }

  async function selectFood(fdcId: number) {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        `${API_URL}/foods/${fdcId}`
      );

      if (!response.ok) {
        throw new Error('Food details failed');
      }

      const data = await response.json();
      setSelectedFood(data);
    } catch {
      setError('Could not load nutrition information.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>AI Nutrition Coach</Text>

      <Text style={styles.subtitle}>
        Search USDA Food Database
      </Text>

      <TextInput
        style={styles.input}
        placeholder="Enter food name, e.g. broccoli"
        value={query}
        onChangeText={setQuery}
        onSubmitEditing={searchFoods}
      />

      <Button
        title="Search Food"
        onPress={searchFoods}
      />

      {loading && (
        <ActivityIndicator style={styles.loading} />
      )}

      {!!error && (
        <Text style={styles.error}>{error}</Text>
      )}

      {foods.map((food) => (
        <View key={food.fdcId} style={styles.food}>
          <Button
            title={food.description}
            onPress={() => selectFood(food.fdcId)}
          />
        </View>
      ))}

      {selectedFood && (
        <View style={styles.details}>
          <Text style={styles.heading}>
            {selectedFood.foodName}
          </Text>

          <Text>Nutrition per 100 g:</Text>

          {Object.entries(
            selectedFood.nutrientsPer100g || {}
          ).map(([name, value]) => (
            <Text key={name}>
              {name}: {String(value)}
            </Text>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 24,
    paddingTop: 60,
    backgroundColor: '#fff',
    flexGrow: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  subtitle: {
    fontSize: 16,
    marginVertical: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#aaa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  loading: {
    marginTop: 20,
  },
  error: {
    color: 'red',
    marginTop: 16,
  },
  food: {
    marginTop: 12,
  },
  details: {
    marginTop: 24,
    padding: 16,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },
  heading: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 12,
  },
});
