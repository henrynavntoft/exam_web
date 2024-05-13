let markers = {};

function mapPins(items) {
  try {
    items = JSON.parse(items);
  } catch (e) {
    console.error("Error parsing items:", e);
    return;
  }

  let lastOpenedPopup = null;

  items.forEach((item) => {
    const popup = new mapboxgl.Popup({ offset: 50 }).setHTML(
      `<div class="flex flex-col gap-2 p-2 rounded-lg">
                <h3 class="text-xl">${item.item_name}</h3>
                <p>${item.item_description}</p>
                <button>View property</button>
            </div>`
    );

    const marker = new mapboxgl.Marker()
      .setLngLat([item.item_lon, item.item_lat])
      .setPopup(popup)
      .addTo(map);

    markers[item.item_pk] = marker;

    marker.getElement().addEventListener("click", () => {
      if (lastOpenedPopup === popup && popup.isOpen()) {
        popup.remove();
      } else {
        popup.addTo(map);
        map.flyTo({ center: [item.item_lon, item.item_lat], zoom: 14 });
      }
      lastOpenedPopup = popup;
    });
  });
}

// FOR MARKER CLICK
const itemsContainer = document.getElementById("items"); // Adjust the ID according to your actual container

itemsContainer.addEventListener("click", function (event) {
  // Check if the clicked element or one of its parents is an item
  let targetElement = event.target;
  while (targetElement && !targetElement.id.startsWith("item-")) {
    targetElement = targetElement.parentNode;
  }

  if (targetElement && targetElement.id.startsWith("item-")) {
    const itemPk = targetElement.id.split("-")[1]; // Extract item_pk
    const marker = markers[itemPk];

    if (marker) {
      const popup = marker.getPopup();
      if (!popup.isOpen()) {
        popup.addTo(map);
        map.flyTo({
          center: marker.getLngLat(),
          zoom: 15,
        });
      } else {
        popup.remove(); // Optionally toggle the popup off if it's already open
      }
    }
  }
});
