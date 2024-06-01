let markers = {};
let lastOpenedPopup = null;

function managePopup(popup, marker) {
  if (
    lastOpenedPopup &&
    lastOpenedPopup.isOpen() &&
    lastOpenedPopup !== popup
  ) {
    lastOpenedPopup.remove(); // Close the currently open popup if it's not the same as the new one
  }
  if (!popup.isOpen()) {
    popup.addTo(map);
    map.flyTo({ center: marker.getLngLat(), zoom: 14 });
  }
  lastOpenedPopup = popup; // Update the last opened popup reference
}

function mapPins(items) {
  try {
    items = JSON.parse(items);
  } catch (e) {
    console.error("Error parsing items:", e);
    return;
  }

  items.forEach((item) => {
    const popup = new mapboxgl.Popup({ offset: 40 }).setHTML(
      `<div class="flex flex-col gap-2 p-2 rounded-lg">
        <img src="images/${item.item_images[0]}" alt="${item.item_name}" class="w-full h-32 object-cover rounded-lg">
        <h3 class="text-xl">${item.item_name}</h3>
        <p>Description: ${item.item_description}</p>
        <p>Price per night: <b>${item.item_price_per_night}</b> DKK</p>
        <button><a href="property/${item.item_pk}">View Property</a></button>
      </div>`
    );

    const marker = new mapboxgl.Marker()
      .setLngLat([item.item_lon, item.item_lat])
      .setPopup(popup)
      .addTo(map);

    markers[item.item_pk] = marker;

    marker.getElement().addEventListener("click", () => {
      managePopup(popup, marker);
    });
  });
}

document.getElementById("items").addEventListener("click", function (event) {
  let targetElement = event.target;
  while (targetElement && !targetElement.id.startsWith("item-")) {
    targetElement = targetElement.parentNode;
  }

  if (targetElement && targetElement.id.startsWith("item-")) {
    const itemPk = targetElement.id.split("-")[1];
    const marker = markers[itemPk];

    if (marker) {
      managePopup(marker.getPopup(), marker);
    }
  }
});
