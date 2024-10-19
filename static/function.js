function updateTable(movies) {
    const tableBody = $('#movies-table');
    // tableBody.empty();
    movies.forEach(movie => {
        const row = `
            <tr>
                <td>${movie.id}</td>
                <td>
                    <a href="${movie.url}" target="_blank">
                        <img alt="${movie.title}" src="${movie.picture}" width="105" height="160">
                    </a>
                </td>
                <td><a href="${movie.url}" target="_blank">${movie.title}</a></td>
                <td>${movie.rating_IMDb}</td>
                <td>${movie.original_name}</td>
                <td>${movie.release}</td>
                <td>${movie.age_limit}</td>
                <td>${movie.genre}</td>
                <td>${movie.country}</td>
                <td>${movie.rating_film_ru}</td>
                <td>${movie.rating_spectators}</td>
            </tr>`;
        tableBody.append(row);
    });
}

// Загрузка фильмов при загрузке страницы
$(document).ready(function() {
    $.ajax({
        url: "/movies",
        method: "GET",
        success: function(movies) {
            updateTable(movies);
            },
        error: function(err) {
            console.error("Ошибка при загрузке фильмов: ", err);
        }
    });
});

// Загрузка новых фильмов при нажатии на кнопку
$('#load-movies').on('click', function() {
    // Показать индикатор загрузки
    $('#loading-spinner').show();
    $.ajax({
        url: "/load",
        method: "POST",
        success: function(movies) {
            updateTable(movies);
        },
        complete: function() {
            // Скрыть индикатор загрузки после завершения
            $('#loading-spinner').hide();
        },
        error: function(err) {
            console.error("Ошибка при загрузке фильмов: ", err);
            // Скрыть индикатор даже при ошибке
            $('#loading-spinner').hide();
        }
    });
});

// Сортировка
$(document).ready(function() {
    $('th').click(function() {
        const table = $(this).parents('table').eq(0);
        let rows = table.find('tr:gt(0)').toArray().sort(comparer($(this).index()));
        if (!this.asc) {
            rows = rows.reverse();
        }
        table.children('tbody').empty().html(rows);
    });
});

function comparer(index) {
    return function(a, b) {
        const valA = getCellValue(a, index);
        const valB = getCellValue(b, index);
        return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.localeCompare(valB);
    };
}

function getCellValue(row, index) {
    return $(row).children('td').eq(index).text();
}