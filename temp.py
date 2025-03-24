sorted_data = dict(
    sorted(
        data.items(),
        key=lambda x: (
            x[0][2] < 0,  # Prioritize positive values first
            -abs(x[0][2]) if x[0][2] < 0 else -x[0][2]  # Reverse order
        )
    )
)