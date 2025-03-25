selectedCells = selectedCells.filter((cell, index, self) =>
    index === self.findIndex(c =>
        c[0] === cell[0] && c[1] === cell[1] && c[2] === cell[2]
    )
);
