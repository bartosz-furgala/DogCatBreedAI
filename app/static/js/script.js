document.addEventListener('DOMContentLoaded', () => {
	const imageUpload = document.getElementById('imageUpload')
	const selectImageButton = document.getElementById('selectImageButton')
	const imageFileName = document.getElementById('imageFileName')
	const imagePreview = document.getElementById('imagePreview')
	const analyzeButton = document.getElementById('analyzeButton')

	const loadingIndicator = document.getElementById('loadingIndicator')
	const animalTypeResults = document.getElementById('animalTypeResults')
	const animalTypeSpan = document.getElementById('animalType')
	const animalConfidenceSpan = document.getElementById('animalConfidence')
	const animalTypeErrorP = document.getElementById('animalTypeError')

	const breedResults = document.getElementById('breedResults')
	const breedListUl = document.getElementById('breedList')
	const breedErrorP = document.getElementById('breedError')

	const dogAgeBox = document.getElementById('dogAgeResult')
	const dogAgeText = document.getElementById('dogAgeText')

	let selectedFile = null

	selectImageButton.addEventListener('click', () => {
		imageUpload.click()
	})

	imageUpload.addEventListener('change', event => {
		selectedFile = event.target.files[0]
		resetResults(false)
		if (selectedFile) {
			imageFileName.textContent = selectedFile.name
			imagePreview.src = URL.createObjectURL(selectedFile)
			imagePreview.style.display = 'block'
			analyzeButton.disabled = false
		} else {
			imageFileName.textContent = 'Brak pliku'
			imagePreview.src = '#'
			imagePreview.style.display = 'none'
			analyzeButton.disabled = true
		}
	})

	analyzeButton.addEventListener('click', async () => {
		if (!selectedFile) {
			alert('Proszę najpierw wybrać zdjęcie!')
			return
		}

		resetResults(true)
		loadingIndicator.style.display = 'block'
		analyzeButton.disabled = true

		const formData = new FormData()
		formData.append('file', selectedFile)

		try {
			const response = await fetch('/predict_animal_type/', {
				method: 'POST',
				body: formData,
			})
			const result = await response.json()

			if (response.ok) {
				const displayedAnimalType = result.animal_type || 'Nieokreślony'
				const confidence = result.animal_confidence || 0

				if (confidence < 0.75) {
					animalTypeErrorP.textContent =
						'Nie udało się rozpoznać zwierzęcia. Upewnij się, że na zdjęciu jest tylko pies lub kot.'
					animalTypeErrorP.style.display = 'block'
					animalTypeResults.style.display = 'block'
					loadingIndicator.style.display = 'none'
					analyzeButton.disabled = false

					return
				}

				animalTypeSpan.textContent = displayedAnimalType
				animalConfidenceSpan.textContent = `${(confidence * 100).toFixed(2)}%`
				animalTypeResults.style.display = 'block'
			} else {
				animalTypeErrorP.textContent = `Błąd typu zwierzęcia: ${result.error || 'Nieznany błąd.'}`
				animalTypeErrorP.style.display = 'block'
				animalTypeResults.style.display = 'block'
				loadingIndicator.style.display = 'none'
				analyzeButton.disabled = false
			}
		} catch (error) {
			animalTypeErrorP.textContent = `Błąd połączenia: ${error.message || error}`
			animalTypeErrorP.style.display = 'block'
			animalTypeResults.style.display = 'block'
			loadingIndicator.style.display = 'none'
			analyzeButton.disabled = false
		}

		try {
			const response = await fetch('/predict_breeds/', {
				method: 'POST',
				body: formData,
			})
			const result = await response.json()

			if (response.ok) {
				// Wiek psa (jeśli dostępny)
				if (
					result.dog_age_prediction &&
					result.dog_age_prediction.prediction &&
					animalTypeSpan.textContent.toLowerCase().includes('pies')
				) {
					dogAgeText.textContent = result.dog_age_prediction.prediction
					dogAgeBox.style.display = 'block'
				}

				// Rasy
				if (result.breeds && result.breeds.length > 0) {
					const minConfidence = 0.1
					const filteredBreeds = result.breeds.filter(breed => breed.confidence >= minConfidence)
					filteredBreeds.sort((a, b) => b.confidence - a.confidence)
					const top3Breeds = filteredBreeds.slice(0, 3)

					if (top3Breeds.length > 0) {
						top3Breeds.forEach(breed => {
							const li = document.createElement('li')
							li.textContent = `${breed.name} (${(breed.confidence * 100).toFixed(2)}%)`
							breedListUl.appendChild(li)
						})
					} else {
						const li = document.createElement('li')
						li.textContent = 'Brak sugerowanych ras.'
						breedListUl.appendChild(li)
					}
				} else {
					const li = document.createElement('li')
					li.textContent = 'Brak sugerowanych ras.'
					breedListUl.appendChild(li)
				}
				breedResults.style.display = 'block'
			} else {
				breedErrorP.textContent = `Błąd ras: ${result.error || 'Nieznany błąd.'}`
				breedErrorP.style.display = 'block'
				breedResults.style.display = 'block'
			}
		} catch (error) {
			breedErrorP.textContent = `Błąd połączenia (rasy): ${error.message || error}`
			breedErrorP.style.display = 'block'
			breedResults.style.display = 'block'
		} finally {
			loadingIndicator.style.display = 'none'
			analyzeButton.disabled = false
		}
	})

	function resetResults(keepLoaderVisible = false) {
		animalTypeSpan.textContent = '--'
		animalConfidenceSpan.textContent = '--'
		breedListUl.innerHTML = ''
		dogAgeText.textContent = ''
		dogAgeBox.style.display = 'none'
		animalTypeErrorP.style.display = 'none'
		animalTypeErrorP.textContent = ''
		breedErrorP.style.display = 'none'
		breedErrorP.textContent = ''
		if (!keepLoaderVisible) {
			loadingIndicator.style.display = 'none'
		}
		animalTypeResults.style.display = 'none'
		breedResults.style.display = 'none'
	}
})
