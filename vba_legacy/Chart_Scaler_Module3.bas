Sub EscalaAtivos5()

    Dim nome As String
    
    Application.ScreenUpdating = False
    
    ActiveSheet.ChartObjects("Gráfico 5").Activate
    
    ActiveChart.Axes(xlValue, 1).Select
    
    With ActiveChart.Axes(xlValue, 1)
        .Crosses = xlMinimum - 0.1
        .MinimumScale = Range("AF10").Value
        .MaximumScale = Range("AF11").Value
        .MajorUnit = Range("AF6")
        .ReversePlotOrder = False
        .ScaleType = xlLinear
        .DisplayUnit = xlNone
    End With
    
    ActiveChart.Axes(xlCategory, 1).Select
      
    With ActiveChart.Axes(xlCategory, 1)
        '.Crosses = xlMinimum
        .CategoryType = xlTimeScale
        .MajorUnit = Range("J7").Value
        '.BaseUnitIsAuto = True
        .MinimumScale = Range("H7").Value
        .MaximumScale = Range("I7").Value
        .TickLabels.Orientation = 45
        .ReversePlotOrder = False

    End With
    
    ActiveSheet.ChartObjects("Gráfico 6").Activate
    
    ActiveChart.Axes(xlValue, 1).Select
    
    With ActiveChart.Axes(xlValue, 1)
        .Crosses = xlMinimum - 0.1
        .MinimumScale = Range("AC5").Value
        .MaximumScale = Range("AC7").Value
        '.MajorUnit = Range("AC3")
        .BaseUnitIsAuto = True
        .ReversePlotOrder = False
        .ScaleType = xlLinear
        .DisplayUnit = xlNone
    End With
    
    ActiveChart.Axes(xlCategory, 1).Select
      
    With ActiveChart.Axes(xlCategory, 1)
        '.Crosses = xlMinimum
        .CategoryType = xlTimeScale
        .MajorUnit = Range("J7").Value
        '.BaseUnitIsAuto = True
        .MinimumScale = Range("H7").Value
        .MaximumScale = Range("I7").Value
        .TickLabels.Orientation = 45
        .ReversePlotOrder = False

    End With
    
    
     ActiveSheet.ChartObjects("Gráfico 4").Activate
    
    ActiveChart.Axes(xlValue, 1).Select
    
    With ActiveChart.Axes(xlValue, 1)
        .Crosses = xlMinimum - 0.1
        .MinimumScale = Range("AM4").Value
        .MaximumScale = Range("AM6").Value
        '.MajorUnit = Range("AC3")
        .BaseUnitIsAuto = True
        .ReversePlotOrder = False
        .ScaleType = xlLinear
        .DisplayUnit = xlNone
    End With
    
    ActiveChart.Axes(xlCategory, 1).Select
      
    With ActiveChart.Axes(xlCategory, 1)
        '.Crosses = xlMinimum
        .CategoryType = xlTimeScale
        .MajorUnit = Range("J7").Value
        '.BaseUnitIsAuto = True
        .MinimumScale = Range("H7").Value
        .MaximumScale = Range("I7").Value
        .TickLabels.Orientation = 45
        .ReversePlotOrder = False

    End With
    

    Application.ScreenUpdating = True

End Sub